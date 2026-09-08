package authz

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/openfga"
	"github.com/xcy/permission-center/internal/store"
)

// DataPlane 数据级授权：策略 scope → OpenFGA 关系（Write）+ check/filter
// 自研翻译/适配层：数据策略（集合式/关系式/属性式）→ OpenFGA 关系与本地求值
type DataPlane struct {
	ofga  *openfga.Client
	res   *store.ResourceRepo
	users *store.UserRepo
	grps  *store.GroupRepo
	clis  *store.AppRepo
	pol   *store.PolicyRepo
}

func NewDataPlane(ofga *openfga.Client, res *store.ResourceRepo, users *store.UserRepo, grps *store.GroupRepo, clis *store.AppRepo, pol *store.PolicyRepo) *DataPlane {
	return &DataPlane{ofga: ofga, res: res, users: users, grps: grps, clis: clis, pol: pol}
}

// EnsureSchema 幂等初始化：store + 授权模型
func (d *DataPlane) EnsureSchema(ctx context.Context) error {
	if err := d.ofga.EnsureStore(ctx, "iam"); err != nil {
		return fmt.Errorf("ensure openfga store: %w", err)
	}
	return d.ofga.EnsureModel(ctx, openfga.ModelDefs())
}

// PublishPolicy 数据策略发布：集合式 scope → 写 OpenFGA 关系
// 关系式/属性式无需物化（动态 Check / Go 求值）
func (d *DataPlane) PublishPolicy(ctx context.Context, p *model.Policy) error {
	ids, ok := scopeInstanceIDs(p)
	if !ok {
		return nil
	}
	subj, err := d.subjectKey(ctx, p)
	if err != nil {
		return err
	}
	rel := openfga.OpToRelation(scopeOperation(p))
	insts, err := d.res.InstancesByIDs(ids)
	if err != nil {
		return err
	}
	model, err := d.res.ModelByCode(scopeModelCode(p))
	if err != nil {
		return err
	}
	for _, inst := range insts {
		obj := fmt.Sprintf("%s:%s", model.Code, inst.ExternalID)
		if err := d.ofga.WriteTuple(ctx, subj, rel, obj); err != nil {
			return err
		}
	}
	return nil
}

// RevokePolicy 撤销数据策略：删除对应关系（防关系图膨胀）
func (d *DataPlane) RevokePolicy(ctx context.Context, p *model.Policy) error {
	ids, ok := scopeInstanceIDs(p)
	if !ok {
		return nil
	}
	subj, err := d.subjectKey(ctx, p)
	if err != nil {
		return err
	}
	rel := openfga.OpToRelation(scopeOperation(p))
	insts, err := d.res.InstancesByIDs(ids)
	if err != nil {
		return err
	}
	model, err := d.res.ModelByCode(scopeModelCode(p))
	if err != nil {
		return err
	}
	for _, inst := range insts {
		d.ofga.DeleteTuple(ctx, subj, rel, fmt.Sprintf("%s:%s", model.Code, inst.ExternalID))
	}
	return nil
}

// CheckInstance 点操作 = Casbin(动作) + OpenFGA Check(实例) / 属性求值
// 短路：无动作权限不查 OpenFGA
func (d *DataPlane) CheckInstance(ctx context.Context, userKey, actionCode, modelCode, externalID, operation string, matchedPids []string) (bool, error) {
	rel := openfga.OpToRelation(operation)
	obj := fmt.Sprintf("%s:%s", modelCode, externalID)
	allow := false
	for _, pid := range matchedPids {
		if strings.HasPrefix(pid, "role:") || strings.HasPrefix(pid, "gp:") {
			continue // 角色/组权限定义行无数据 scope
		}
		id, err := strconv.ParseUint(pid, 10, 64)
		if err != nil {
			continue
		}
		p, err := d.pol.ByID(id)
		if err != nil {
			continue
		}
		if p.ResourceScope == nil {
			return true, nil // 无数据范围 → 动作级放行（全量）
		}
		if m := scopeModelCode(p); m != "" && m != modelCode {
			continue
		}
		switch {
		case p.ResourceScope["instance_ids"] != nil || p.ResourceScope["relation"] != nil:
			relToUse := rel
			if p.ResourceScope["relation"] != nil {
				relToUse, _ = p.ResourceScope["relation"].(string)
			}
			ok, err := d.ofga.Check(ctx, userKey, relToUse, obj)
			if err != nil {
				return false, err
			}
			if ok {
				allow = true
			}
		case p.ResourceScope["condition"] != nil:
			// 属性式：对实例 attributes 求值
			if m, err := d.res.ModelByCode(modelCode); err == nil {
				if inst, err := d.res.InstanceByExternal(m.ID, externalID); err == nil {
					if cond, ok := p.ResourceScope["condition"].(map[string]any); ok {
						if evalAttrCond(cond, inst.Attributes) {
							allow = true
						}
					}
				}
			}
		}
	}
	return allow, nil
}

// FilterResult filter 结果（含实例集 + 维度级范围条件）
type FilterResult struct {
	InstanceIDs    []string       `json:"instance_ids"`
	ScopeCondition map[string]any `json:"scope_condition,omitempty"` // 维度级范围条件供下游拼接
}

// Filter 列表 = OpenFGA ListObjects → 允许实例集 + 维度级范围条件
func (d *DataPlane) Filter(ctx context.Context, userKey, actionCode, modelCode, operation string, matchedPids []string) (*FilterResult, error) {
	rel := openfga.OpToRelation(operation)
	set := map[string]bool{}
	fullAccess := false
	var dimensionConditions []map[string]any

	for _, pid := range matchedPids {
		if strings.HasPrefix(pid, "role:") || strings.HasPrefix(pid, "gp:") {
			continue
		}
		id, err := strconv.ParseUint(pid, 10, 64)
		if err != nil {
			continue
		}
		p, err := d.pol.ByID(id)
		if err != nil {
			continue
		}
		if p.ResourceScope == nil {
			fullAccess = true
			continue
		}
		if m := scopeModelCode(p); m != "" && m != modelCode {
			continue
		}

		switch {
		// 维度/属性级范围（新增维度级 scope）
		case p.ResourceScope["dimension"] != nil:
			dim, _ := p.ResourceScope["dimension"].(string)
			vals, _ := p.ResourceScope["values"].([]any)
			if dim != "" && len(vals) > 0 {
				dimensionConditions = append(dimensionConditions, map[string]any{
					"field":  dim,
					"op":     "in",
					"values": vals,
				})
			}

		// 集合式/关系式：OpenFGA ListObjects
		case p.ResourceScope["instance_ids"] != nil || p.ResourceScope["relation"] != nil:
			relToUse := rel
			if p.ResourceScope["relation"] != nil {
				relToUse, _ = p.ResourceScope["relation"].(string)
			}
			objs, err := d.ofga.ListObjects(ctx, userKey, relToUse, modelCode)
			if err != nil {
				return nil, err
			}
			for _, o := range objs {
				set[o] = true
			}
		}
	}

	if fullAccess {
		insts, err := d.allInstances(modelCode)
		if err != nil {
			return nil, err
		}
		for _, o := range insts {
			set[o] = true
		}
	}

	out := make([]string, 0, len(set))
	for o := range set {
		out = append(out, o)
	}

	result := &FilterResult{InstanceIDs: out}
	// 合并维度级条件为 AND 逻辑
	if len(dimensionConditions) > 0 {
		result.ScopeCondition = map[string]any{
			"logic": "and",
			"rules": dimensionConditions,
		}
	}
	return result, nil
}

// 主体 key（OpenFGA）：user:username / group:{id}#member / service:{client_id}
func (d *DataPlane) subjectKey(ctx context.Context, p *model.Policy) (string, error) {
	switch p.SubjectType {
	case model.SubjectUser:
		u, err := d.users.ByID(p.SubjectID)
		if err != nil {
			return "", err
		}
		return "user:" + u.Username, nil
	case model.SubjectGroup:
		return fmt.Sprintf("group:%d#member", p.SubjectID), nil
	case model.SubjectService:
		c, err := d.clis.ClientByRowID(p.SubjectID)
		if err != nil {
			return "", err
		}
		return "service:" + c.ClientID, nil
	default:
		return "", fmt.Errorf("unsupported subject type")
	}
}

func (d *DataPlane) allInstances(modelCode string) ([]string, error) {
	m, err := d.res.ModelByCode(modelCode)
	if err != nil {
		return nil, err
	}
	insts, _, err := d.res.Instances(m.ID, 0, 10000)
	if err != nil {
		return nil, err
	}
	out := make([]string, 0, len(insts))
	for _, i := range insts {
		out = append(out, fmt.Sprintf("%s:%s", modelCode, i.ExternalID))
	}
	return out, nil
}

func scopeModelCode(p *model.Policy) string {
	if v, ok := p.ResourceScope["model"].(string); ok {
		return v
	}
	return ""
}

// scopeInstanceIDs 兼容 []uint64（Go 构造）与 []any（JSON 反序列化）
func scopeInstanceIDs(p *model.Policy) ([]uint64, bool) {
	raw, ok := p.ResourceScope["instance_ids"]
	if !ok {
		return nil, false
	}
	var ids []uint64
	switch v := raw.(type) {
	case []uint64:
		ids = v
	case []any:
		for _, x := range v {
			if n, err := toUint(x); err == nil {
				ids = append(ids, n)
			}
		}
	default:
		return nil, false
	}
	return ids, len(ids) > 0
}

func scopeOperation(p *model.Policy) string {
	if v, ok := p.ResourceScope["operation"].(string); ok {
		return v
	}
	return "read"
}

func toUint(v any) (uint64, error) {
	switch n := v.(type) {
	case float64:
		return uint64(n), nil
	case int:
		return uint64(n), nil
	case string:
		return strconv.ParseUint(n, 10, 64)
	default:
		return 0, fmt.Errorf("cannot convert %T", v)
	}
}
