package authz

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
)

// DataPlane 1.5 数据级判定：范围谓词 × 权威行（点查取材，T2/T3）。
//
// 投影机制退役（1.5 T3，方案 §2/§9 #1）：OpenFGA 关系检查、投影存在性前置、
// 新鲜度门槛（确认制状态机）、force-remote 强一致档均已移除——取材一律点查（material 包），
// 行实时、不过新鲜度门（无新鲜度税）；上游不可达=点查失败 fail-closed（材料层，非本层）。
type DataPlane struct {
	pol *store.PolicyRepo
}

func NewDataPlane(pol *store.PolicyRepo) *DataPlane { return &DataPlane{pol: pol} }

// CheckRow 范围谓词求值（T2 引入，T3 收口为唯一数据级判定路径）：
//   - ResourceScope=nil → 全量（动作级已放行即放行）
//   - condition（属性式）→ 对权威行/信封伪行求值（evalAttrCond）
//   - instance_ids（集合式/勾选实例）→ 点查行 id 与集合比对（1.5 语义：
//     外部 id 字符串直接比、历史数字项比外部 id 尾号；关系元组引擎已退役，
//     demo 存量集合为空、无迁移面）
//   - relation（关系式）→ 预留无入口（方案 §4.5），出现即不匹配
//
// userKey 保留为通道合同参数（主体资格由动作级 Casbin 判定，本层不再消费）。
// row==nil → data_missing（fail-closed 拒单条）。返回语义与旧 CheckInstance 一致。
func (d *DataPlane) CheckRow(userKey, modelCode, externalID string, row map[string]any, matchedPids []string) (bool, string, error) {
	_ = userKey
	if row == nil {
		return false, "data_missing", nil
	}
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
			return true, "", nil // 无数据范围 → 动作级放行（全量）
		}
		if sc := scopeModelCode(p); sc != "" && sc != modelCode {
			continue
		}
		switch {
		case p.ResourceScope["instance_ids"] != nil:
			if externalID == "" {
				continue // 创建类无实例，集合式不匹配
			}
			if instanceSetContains(p.ResourceScope["instance_ids"], externalID) {
				allow = true
			}
		case p.ResourceScope["condition"] != nil:
			if cond, ok := p.ResourceScope["condition"].(map[string]any); ok {
				if evalAttrCond(cond, row) {
					allow = true
				}
			}
		}
	}
	return allow, "", nil
}

// instanceSetContains 集合成员比对：外部 id 字符串直接比；历史数字项比外部 id 尾号
// （兼容早期 instance_ids 存投影数字 id 的写法——"host-4" 尾号 4）
func instanceSetContains(raw any, externalID string) bool {
	suffix := externalID
	if i := strings.LastIndex(externalID, "-"); i >= 0 {
		suffix = externalID[i+1:]
	}
	cmp := func(x any) bool {
		switch t := x.(type) {
		case string:
			return t == externalID || t == suffix
		case float64: // JSONB 数字
			return fmt.Sprintf("%v", t) == suffix
		case int:
			return strconv.Itoa(t) == suffix
		case uint64:
			return strconv.FormatUint(t, 10) == suffix
		}
		return false
	}
	switch v := raw.(type) {
	case []any:
		for _, x := range v {
			if cmp(x) {
				return true
			}
		}
	case []string:
		for _, x := range v {
			if x == externalID || x == suffix {
				return true
			}
		}
	case []uint64:
		for _, x := range v {
			if strconv.FormatUint(x, 10) == suffix {
				return true
			}
		}
	}
	return false
}

// scopeModelCode 策略数据范围绑定的模型域（scope["model"]，空=不限域）
func scopeModelCode(p *model.Policy) string {
	if v, ok := p.ResourceScope["model"].(string); ok {
		return v
	}
	return ""
}
