package store

import (
	"fmt"
	"regexp"
	"sort"
	"strings"

	"github.com/xcy/permission-center/internal/model"
	"gorm.io/gorm"
)

// AccessRepo 权限点 / 板块模板 / 角色
type AccessRepo struct{ db *gorm.DB }

func NewAccessRepo(db *gorm.DB) *AccessRepo { return &AccessRepo{db: db} }

// --- Actions ---

func (r *AccessRepo) CreateActions(actions []*model.Action) error {
	return r.db.CreateInBatches(actions, 100).Error
}

func (r *AccessRepo) UpsertAction(a *model.Action) error {
	// 按 app+code 幂等：已存在则更新
	var existing model.Action
	err := r.db.Where("app_id = ? AND code = ?", a.AppID, a.Code).First(&existing).Error
	if err == gorm.ErrRecordNotFound {
		return r.db.Create(a).Error
	}
	if err != nil {
		return err
	}
	existing.Name, existing.Resource, existing.Operation = a.Name, a.Resource, a.Operation
	existing.Method, existing.Path = a.Method, a.Path
	existing.IsGeneric, existing.ResourceSlot = a.IsGeneric, a.ResourceSlot
	// 接口契约（v12）：请求/响应示例（非空才覆盖，避免空文档清掉已有示例）
	if a.ReqExample != "" {
		existing.ReqExample = a.ReqExample
	}
	if a.RespExample != "" {
		existing.RespExample = a.RespExample
	}
	// v1.5：回填既有行（含 ID）——调用方（如待确认落表）需要真实主键，否则拿到 ID=0
	*a = existing
	return r.db.Save(a).Error
}

// Actions 应用的权限点清单（排除通用接口路由：PEP 提示，非可授予权限点；排除归档=可查不可用）
func (r *AccessRepo) Actions(appID uint64) ([]model.Action, error) {
	var as []model.Action
	if err := r.db.Where("app_id = ? AND is_generic = ? AND COALESCE(status,'') <> ?",
		appID, false, "archived").Order("resource, operation").Find(&as).Error; err != nil {
		return nil, err
	}
	return as, nil
}

// AllActions 含通用路由（PEP 解析用）
func (r *AccessRepo) AllActions(appID uint64) ([]model.Action, error) {
	var as []model.Action
	if err := r.db.Where("app_id = ?", appID).Find(&as).Error; err != nil {
		return nil, err
	}
	return as, nil
}

func (r *AccessRepo) ActionsByIDs(ids []uint64) ([]model.Action, error) {
	var as []model.Action
	if err := r.db.Where("id IN ?", ids).Find(&as).Error; err != nil {
		return nil, err
	}
	return as, nil
}

func (r *AccessRepo) ActionByCode(appID uint64, code string) (*model.Action, error) {
	var a model.Action
	if err := r.db.Where("app_id = ? AND code = ?", appID, code).First(&a).Error; err != nil {
		return nil, err
	}
	return &a, nil
}

func (r *AccessRepo) ActionByID(id uint64) (*model.Action, error) {
	var a model.Action
	if err := r.db.First(&a, id).Error; err != nil {
		return nil, err
	}
	return &a, nil
}

// ActionByRequest PEP 请求→action 映射：按 method+path 匹配权限点（网关 forwardAuth 回调用）
// 路径模式如 /api/v1/hosts/{id}，{param} 通配任意路径段
// 通用接口（§6.2）：字面匹配优先；无字面则走路径模板解析（资源槽位）+ X-Resource-Type 兜底，
// 解析出的真实资源拼出具体权限点（cmdb:host:list）返回；写操作无法落具体资源 → 拒绝（ErrNotFound）
func (r *AccessRepo) ActionByRequest(appID uint64, method, path, resourceTypeHeader string) (*model.Action, error) {
	t := r.ResolveActionSteps(appID, method, path, resourceTypeHeader)
	if t.Action == nil {
		return nil, ErrNotFound
	}
	return t.Action, nil
}

// ResolveStep PEP 解析单步（链路追踪 / 解析工作台展示）
type ResolveStep struct {
	Step   string         `json:"step"`
	Label  string         `json:"label"`
	OK     bool           `json:"ok"`
	Detail map[string]any `json:"detail,omitempty"`
}

// ResolveTrace PEP 请求→action 解析全流程（黑盒可见化核心）
type ResolveTrace struct {
	AppID            uint64        `json:"app_id"`
	Method           string        `json:"method"`
	Path             string        `json:"path"`
	ResourceType     string        `json:"resource_type"` // X-Resource-Type
	Steps            []ResolveStep `json:"steps"`
	Action           *model.Action `json:"action,omitempty"`
	MatchMode        string        `json:"match_mode"`        // literal|template|header|none
	PathPattern      string        `json:"path_pattern"`      // 命中的路径模式
	ResolvedResource string        `json:"resolved_resource"` // 通用接口解析出的资源
}

// ResolveActionSteps 步骤化解析：字面优先 → 通用模板（槽位/X-Resource-Type）→ 真实权限点
// 匹配顺序 = specificity 钉死（§3.8）：方法先比（查询已过滤）→ 静态段数多者优先 →
// 同数逐段从左比（静态段 > 参数段）→ 全等按登记序（id 升序）；归档动作不参与解析。
func (r *AccessRepo) ResolveActionSteps(appID uint64, method, path, resourceTypeHeader string) *ResolveTrace {
	method = strings.ToUpper(method)
	trace := &ResolveTrace{
		AppID: appID, Method: method, Path: path, ResourceType: resourceTypeHeader,
		Steps: []ResolveStep{}, MatchMode: "none",
	}
	var acts []model.Action
	if err := r.db.Where("app_id = ? AND method = ? AND COALESCE(status,'') <> ?",
		appID, method, "archived").Find(&acts).Error; err != nil {
		trace.Steps = append(trace.Steps, ResolveStep{Step: "error", Label: "查询权限点失败", OK: false, Detail: map[string]any{"error": err.Error()}})
		return trace
	}
	literals := make([]model.Action, 0)
	generics := make([]model.Action, 0)
	appCode := ""
	for _, a := range acts {
		if a.IsGeneric {
			generics = append(generics, a)
			if appCode == "" {
				appCode = strings.SplitN(a.Code, ":", 2)[0]
			}
		} else {
			literals = append(literals, a)
		}
	}
	// specificity 排序（§3.8 钉死：静态段多者优先 → 逐段静态>参数 → 登记序）
	sort.SliceStable(literals, func(i, j int) bool { return moreSpecific(literals[i], literals[j]) })
	sort.SliceStable(generics, func(i, j int) bool { return moreSpecific(generics[i], generics[j]) })
	trace.Steps = append(trace.Steps, ResolveStep{
		Step: "list_literal", Label: "扫描该方法的字面权限点",
		OK: len(literals) > 0, Detail: map[string]any{"count": len(literals), "patterns": actionPaths(literals)},
	})
	// 字面匹配优先
	for _, a := range literals {
		if matchPath(a.Path, path) {
			trace.Action = &a
			trace.MatchMode = "literal"
			trace.PathPattern = a.Path
			trace.Steps = append(trace.Steps, ResolveStep{
				Step: "match_literal", Label: "字面匹配命中", OK: true,
				Detail: map[string]any{"pattern": a.Path, "code": a.Code},
			})
			return trace
		}
	}
	trace.Steps = append(trace.Steps, ResolveStep{Step: "no_literal", Label: "无字面匹配，尝试通用接口模板", OK: false})
	trace.Steps = append(trace.Steps, ResolveStep{
		Step: "list_generic", Label: "扫描通用接口模板",
		OK: len(generics) > 0, Detail: map[string]any{"count": len(generics), "templates": genericPaths(generics)},
	})
	// 通用模板：槽位提取 / X-Resource-Type 兜底 → 拼真实权限点
	for _, a := range generics {
		res, ok := resolveGenericResource(&a, path, resourceTypeHeader)
		detail := map[string]any{"pattern": a.Path, "slot": a.ResourceSlot}
		if ok {
			detail["resolved"] = res
		}
		trace.Steps = append(trace.Steps, ResolveStep{
			Step: "try_template", Label: "模板 " + a.Path + " 资源解析", OK: ok, Detail: detail,
		})
		if !ok {
			continue
		}
		realCode := fmt.Sprintf("%s:%s:%s", appCode, res, a.Operation)
		real, err := r.ActionByCode(appID, realCode)
		if err != nil {
			trace.Steps = append(trace.Steps, ResolveStep{
				Step: "no_action", Label: "权限点未声明（该资源不在能力声明中）", OK: false,
				Detail: map[string]any{"real_code": realCode},
			})
			continue
		}
		trace.Action = real
		trace.MatchMode = "template"
		if a.ResourceSlot == "header" {
			trace.MatchMode = "header"
		}
		trace.PathPattern = a.Path
		trace.ResolvedResource = res
		trace.Steps = append(trace.Steps, ResolveStep{
			Step: "match_template", Label: "拼出真实权限点", OK: true,
			Detail: map[string]any{"real_code": real.Code, "resource": res},
		})
		return trace
	}
	trace.Steps = append(trace.Steps, ResolveStep{Step: "result", Label: "无法解析 → deny-by-default", OK: false})
	return trace
}

func actionPaths(acts []model.Action) []string {
	out := make([]string, 0, len(acts))
	for _, a := range acts {
		out = append(out, a.Path)
	}
	return out
}

func genericPaths(acts []model.Action) []string {
	out := make([]string, 0, len(acts))
	for _, a := range acts {
		out = append(out, a.Path+" (slot="+a.ResourceSlot+")")
	}
	return out
}

// resolveGenericResource 从通用路由提取真实资源：
//   - 路径槽位：/api/v1/{model} + /api/v1/hosts → hosts → host
//   - X-Resource-Type 兜底：统一查询入口 /api/v1/entities
//
// 写操作（create/update/delete）无法解析到具体资源 → 失败（调用方按 deny-by-default 拒绝）
func resolveGenericResource(a *model.Action, path, resourceTypeHeader string) (string, bool) {
	if a.ResourceSlot != "" && a.ResourceSlot != "header" {
		if val, ok := slotValueFromPath(a.Path, path); ok && val != "" {
			return singularize(val), true
		}
	}
	if resourceTypeHeader != "" {
		return singularize(resourceTypeHeader), true
	}
	return "", false
}

// slotValueFromPath 从请求路径提取资源槽位值
// pattern /api/v1/{model} + request /api/v1/hosts → hosts
func slotValueFromPath(pattern, path string) (string, bool) {
	psegs := strings.Split(strings.Trim(pattern, "/"), "/")
	segs := strings.Split(strings.Trim(path, "/"), "/")
	if len(psegs) != len(segs) {
		return "", false
	}
	for i := range psegs {
		if strings.HasPrefix(psegs[i], "{") {
			return segs[i], true
		}
	}
	return "", false
}

// singularize 简单复数归一化（hosts→host；ies 结尾 → y）
func singularize(s string) string {
	if strings.HasSuffix(s, "ies") && len(s) > 3 {
		return s[:len(s)-3] + "y"
	}
	if strings.HasSuffix(s, "ses") {
		return s[:len(s)-2]
	}
	if strings.HasSuffix(s, "s") && len(s) > 1 {
		return s[:len(s)-1]
	}
	return s
}

// matchPath /api/v1/hosts/{id} → 匹配 /api/v1/hosts/3
func matchPath(pattern, path string) bool {
	var sb strings.Builder
	sb.WriteString("^")
	for _, seg := range strings.Split(strings.Trim(pattern, "/"), "/") {
		if strings.HasPrefix(seg, "{") {
			sb.WriteString("/[^/]+")
		} else {
			sb.WriteByte('/')
			sb.WriteString(regexp.QuoteMeta(seg))
		}
	}
	sb.WriteString("$")
	return regexp.MustCompile(sb.String()).MatchString(path)
}

// --- 路由 specificity（§3.8 钉死：静态段数多者优先 → 同数逐段从左比（静态>参数）→ 全等按登记序）---

func routeSegs(p string) []string { return strings.Split(strings.Trim(p, "/"), "/") }

func staticSegCount(p string) int {
	n := 0
	for _, s := range routeSegs(p) {
		if s != "" && !strings.HasPrefix(s, "{") {
			n++
		}
	}
	return n
}

// moreSpecific a 是否比 b 更具体（决定谁先参与 matchPath）
func moreSpecific(a, b model.Action) bool {
	ca, cb := staticSegCount(a.Path), staticSegCount(b.Path)
	if ca != cb {
		return ca > cb
	}
	sa, sb := routeSegs(a.Path), routeSegs(b.Path)
	n := len(sa)
	if len(sb) < n {
		n = len(sb)
	}
	for i := 0; i < n; i++ {
		aPar := strings.HasPrefix(sa[i], "{")
		bPar := strings.HasPrefix(sb[i], "{")
		if aPar != bPar {
			return !aPar // 静态段优先（同位比：静态 > 参数）
		}
	}
	if len(sa) != len(sb) {
		return len(sa) > len(sb)
	}
	return a.ID < b.ID // 登记序
}

// --- Templates ---

func (r *AccessRepo) CreateTemplate(t *model.PermissionTemplate) error {
	return r.db.Create(t).Error
}

func (r *AccessRepo) Templates(appID uint64) ([]model.PermissionTemplate, error) {
	var ts []model.PermissionTemplate
	if err := r.db.Where("app_id = ?", appID).Order("sort, id").Find(&ts).Error; err != nil {
		return nil, err
	}
	return ts, nil
}

func (r *AccessRepo) SetTemplateActions(templateID uint64, actionIDs []uint64) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Where("template_id = ?", templateID).Delete(&model.TemplateAction{}).Error; err != nil {
			return err
		}
		for _, aid := range actionIDs {
			if err := tx.Create(&model.TemplateAction{TemplateID: templateID, ActionID: aid}).Error; err != nil {
				return err
			}
		}
		return nil
	})
}

func (r *AccessRepo) TemplateActions(templateID uint64) ([]model.Action, error) {
	var as []model.Action
	err := r.db.
		Joins("JOIN template_actions ta ON ta.action_id = actions.id").
		Where("ta.template_id = ?", templateID).
		Find(&as).Error
	return as, err
}

// --- GroupPermissions（组即角色）---

func (r *AccessRepo) SetGroupPermissions(groupID uint64, actionIDs []uint64) error {
	return r.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Where("group_id = ?", groupID).Delete(&model.GroupPermission{}).Error; err != nil {
			return err
		}
		for _, aid := range actionIDs {
			if err := tx.Create(&model.GroupPermission{GroupID: groupID, ActionID: aid}).Error; err != nil {
				return err
			}
		}
		return nil
	})
}

func (r *AccessRepo) GroupPermissionIDs(groupID uint64) ([]uint64, error) {
	var ids []uint64
	if err := r.db.Model(&model.GroupPermission{}).Where("group_id = ?", groupID).Pluck("action_id", &ids).Error; err != nil {
		return nil, err
	}
	return ids, nil
}

// GroupActionIDsByGroups 批量获取多个组的权限点 ID（去重）
func (r *AccessRepo) GroupActionIDsByGroups(groupIDs []uint64) ([]uint64, error) {
	var ids []uint64
	if err := r.db.Model(&model.GroupPermission{}).Where("group_id IN ?", groupIDs).Distinct("action_id").Pluck("action_id", &ids).Error; err != nil {
		return nil, err
	}
	return ids, nil
}

func (r *AccessRepo) GroupPermissionsByGroupIDs(groupIDs []uint64) ([]model.GroupPermission, error) {
	var gps []model.GroupPermission
	if err := r.db.Where("group_id IN ?", groupIDs).Find(&gps).Error; err != nil {
		return nil, err
	}
	return gps, nil
}
