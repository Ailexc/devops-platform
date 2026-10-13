package api

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/sync"
)

// v1.5 T1 动作码路由表（方案 §3.7 五格登记 / §3.8 路由表三种建法与导入推断 / §3.9 生命周期）
// 路由表本体 = Action 行（Method/Path/Code）；本文件管登记、导入、待确认、迁移、归档。
// 设计红线：推断永远不活在运行期——推断只在导入、预填永不直接生效（Pending 人工确认后落表）。

// routeEntry dict 导入条目（§3.8 建表方式二：中央字典格式；方式三=人工登记=五格 PATCH）
type routeEntry struct {
	Method string `json:"method"`
	Path   string `json:"path"`
	Action string `json:"action"` // 完整三段码 或 resource:verb 简写；空 → 推断进待确认队列
	RW     string `json:"rw"`     // 可选 read|write（空=按动作段推导）
	Name   string `json:"name"`
}

type routeImportReq struct {
	Source  string       `json:"source"` // openapi|dict
	Entries []routeEntry `json:"entries"`
}

// listRoutes 路由表总览：动作行（含归档=可查）+ 当前版本 + 待确认队列 + 迁移记录
func (d *Deps) listRoutes(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	acts, err := d.Access.AllActions(appID)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	pend, _ := d.Access.Pendings(appID, "")
	logs, _ := d.Access.MigrateLogs(appID)
	c.JSON(200, gin.H{
		"items": acts, "version": d.Access.CurrentRouteVersion(appID),
		"pending": pend, "migrations": logs,
	})
}

// importRoutes 导入（§3.8 三种建法的前两种；人工登记=PATCH 五格）
//   - openapi：走既有 OpenAPISyncer（x-action 源头标注 100% 准确，无标注的进推断）
//   - dict：逐条 upsert；action 缺省 → InferRoute 推断入待确认队列（预填永不直接生效）
//
// 落表前挡两类撞车（体检阻断项提前到导入期）：同码挂多路由 / 同路由挂多码。
func (d *Deps) importRoutes(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	app, err := d.Apps.ByID(appID)
	if err != nil {
		c.JSON(404, gin.H{"error": "app not found"})
		return
	}
	var req routeImportReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": "bad body: " + err.Error()})
		return
	}
	uid := d.currentUserID(c)

	switch req.Source {
	case "openapi":
		n, err := d.OpenAPISyncer.Sync(c.Request.Context(), app)
		if err != nil {
			c.JSON(502, gin.H{"error": "openapi sync: " + err.Error()})
			return
		}
		imported := 0
		if v, ok := n["actions"].(int); ok {
			imported = v
		} else if v, ok := n["actions"].(float64); ok {
			imported = int(v)
		}
		v, _ := d.Access.BumpRouteVersion(appID, "openapi", fmt.Sprintf("OpenAPI 导入 %d 条", imported), uid)
		pend, _ := d.Access.Pendings(appID, "")
		c.JSON(200, gin.H{"version": v, "imported": imported, "blocked": []any{}, "pending": pend})
		return

	case "dict":
		if len(req.Entries) == 0 {
			c.JSON(400, gin.H{"error": "entries required"})
			return
		}
		acts, err := d.Access.AllActions(appID)
		if err != nil {
			c.JSON(500, gin.H{"error": err.Error()})
			return
		}
		byRoute := map[string][]model.Action{} // "METHOD path" → 已登记行
		byCode := map[string]model.Action{}
		verbs := []string{}
		for _, a := range acts {
			byRoute[strings.ToUpper(a.Method)+" "+a.Path] = append(byRoute[strings.ToUpper(a.Method)+" "+a.Path], a)
			byCode[a.Code] = a
			if a.Operation != "" {
				verbs = append(verbs, a.Operation)
			}
		}
		verbSet := sync.VerbSet(verbs)

		imported, pendingN := 0, 0
		blocked := []map[string]any{}
		pendOut := []map[string]any{}

		for _, e := range req.Entries {
			method := strings.ToUpper(strings.TrimSpace(e.Method))
			path := strings.TrimSpace(e.Path)
			if method == "" || path == "" || !strings.HasPrefix(path, "/") {
				blocked = append(blocked, map[string]any{
					"method": e.Method, "path": e.Path, "reason": "method/path 非法",
				})
				continue
			}
			routeKey := method + " " + path

			if e.Action != "" { // 显式登记（确认态）
				code := strings.TrimSpace(e.Action)
				if strings.Count(code, ":") == 1 { // 简写 resource:verb → 补 app 段
					code = app.Code + ":" + code
				}
				if err := model.ValidateCodeFormat(code); err != nil {
					blocked = append(blocked, map[string]any{
						"method": method, "path": path, "action": code,
						"reason": err.Error(),
					})
					continue
				}
				// 同码挂多路由
				if prev, ok := byCode[code]; ok &&
					strings.ToUpper(prev.Method)+" "+prev.Path != routeKey {
					blocked = append(blocked, map[string]any{
						"method": method, "path": path, "action": code,
						"reason": fmt.Sprintf("同码挂多路由：已挂 %s %s（如需别名路由走显式登记）",
							prev.Method, prev.Path),
					})
					continue
				}
				// 同路由挂多码
				conflict := false
				for _, prev := range byRoute[routeKey] {
					if prev.Code != code {
						conflict = true
						break
					}
				}
				if conflict {
					blocked = append(blocked, map[string]any{
						"method": method, "path": path, "action": code,
						"reason": "同一路由挂多码（归档旧码或改走迁移）",
					})
					continue
				}
				parts := strings.Split(code, ":")
				rw := strings.ToLower(strings.TrimSpace(e.RW))
				if rw != "read" && rw != "write" {
					rw = sync.OperationRW(parts[2])
				}
				a := &model.Action{
					AppID: appID, Code: code, Name: e.Name,
					Resource: parts[1], Operation: parts[2],
					Method: method, Path: path, RW: rw, Status: model.StatusActive,
				}
				if err := d.Access.UpsertAction(a); err != nil {
					blocked = append(blocked, map[string]any{
						"method": method, "path": path, "action": code,
						"reason": "落表失败: " + err.Error(),
					})
					continue
				}
				byCode[code] = *a
				byRoute[routeKey] = append(byRoute[routeKey], *a)
				imported++
				continue
			}

			// 推断 → 待确认队列（预填永不直接生效，§3.8 ⑤）
			inf := sync.InferRoute(method, path, verbSet)
			code := ""
			if inf.Resource != "" && inf.Verb != "" {
				code = app.Code + ":" + inf.Resource + ":" + inf.Verb
			}
			p := &model.RoutePending{
				AppID: appID, Method: method, Path: path,
				InferredCode: code, RW: inf.RW, Reason: inf.Reason,
			}
			if err := d.Access.AddPending(p); err != nil {
				blocked = append(blocked, map[string]any{
					"method": method, "path": path, "reason": "入队失败: " + err.Error(),
				})
				continue
			}
			pendingN++
			pendOut = append(pendOut, map[string]any{
				"method": method, "path": path, "inferred_code": code,
				"rw": inf.RW, "reason": inf.Reason,
			})
		}

		version := d.Access.CurrentRouteVersion(appID)
		if imported > 0 {
			version, _ = d.Access.BumpRouteVersion(appID, "dict",
				fmt.Sprintf("字典导入 %d 条（待确认 %d）", imported, pendingN), uid)
		}
		c.JSON(200, gin.H{
			"version": version, "imported": imported,
			"pending_count": pendingN, "pending": pendOut, "blocked": blocked,
		})
		return

	default:
		c.JSON(400, gin.H{"error": "source must be openapi|dict"})
	}
}

// confirmPending 待确认队列 → 落表（人工确认；可覆盖推断码）
func (d *Deps) confirmPending(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	pid, _ := strconv.ParseUint(c.Param("pid"), 10, 64)
	p, err := d.Access.PendingByID(pid)
	if err != nil || p.AppID != appID {
		c.JSON(404, gin.H{"error": "pending not found"})
		return
	}
	if p.Status != model.PendPending {
		c.JSON(409, gin.H{"error": "pending already " + p.Status})
		return
	}
	var body struct {
		Code string `json:"code"` // 可选：人工改码
	}
	_ = c.ShouldBindJSON(&body)
	code := strings.TrimSpace(body.Code)
	if code == "" {
		code = p.InferredCode
	}
	if code == "" {
		c.JSON(400, gin.H{"error": "推断不出动作码，须显式提供 code"})
		return
	}
	if err := model.ValidateCodeFormat(code); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	parts := strings.Split(code, ":")
	uid := d.currentUserID(c)
	a := &model.Action{
		AppID: appID, Code: code,
		Resource: parts[1], Operation: parts[2],
		Method: strings.ToUpper(p.Method), Path: p.Path,
		RW: p.RW, Status: model.StatusActive,
	}
	if a.RW != "read" && a.RW != "write" {
		a.RW = sync.OperationRW(parts[2])
	}
	if err := d.Access.UpsertAction(a); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	_ = d.Access.SetPendingStatus(p.ID, model.PendConfirmed)
	v, _ := d.Access.BumpRouteVersion(appID, "manual",
		fmt.Sprintf("待确认落表 %s %s → %s", a.Method, a.Path, code), uid)
	c.JSON(200, gin.H{"action": a, "version": v})
}

// discardPending 丢弃待确认项
func (d *Deps) discardPending(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	pid, _ := strconv.ParseUint(c.Param("pid"), 10, 64)
	p, err := d.Access.PendingByID(pid)
	if err != nil || p.AppID != appID {
		c.JSON(404, gin.H{"error": "pending not found"})
		return
	}
	if err := d.Access.SetPendingStatus(p.ID, model.PendDiscarded); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	c.JSON(200, gin.H{"ok": true})
}

// updateRouteRegistration 五格登记（§3.7 配置页 PATCH）：name/rw/need_data/material/scope_param
// code 不可直接改（改名不存在）→ 409 变更阻断 + 受影响清单，走 migrate-code。
func (d *Deps) updateRouteRegistration(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	rid, _ := strconv.ParseUint(c.Param("rid"), 10, 64)
	a, err := d.Access.ActionByID(rid)
	if err != nil || a.AppID != appID {
		c.JSON(404, gin.H{"error": "route not found"})
		return
	}
	var body struct {
		Name       string         `json:"name"`
		RW         *string        `json:"rw"`
		NeedData   *bool          `json:"need_data"`
		Material   *model.JSONMap `json:"material"`
		ScopeParam *model.JSONMap `json:"scope_param"`
		Code       string         `json:"code"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(400, gin.H{"error": "bad body: " + err.Error()})
		return
	}
	// 变更阻断：code 是被策略引用的字符串，改名=迁移（§3.9 词表规矩 3）
	if body.Code != "" && body.Code != a.Code {
		refs, _ := d.Access.ActionReferences(rid)
		c.JSON(409, gin.H{
			"error":    "code_change_blocked",
			"hint":     "动作码不可直接修改——语义等价的改名走 migrate-code 一键迁移",
			"affected": refs,
		})
		return
	}
	updates := map[string]any{}
	if body.Name != "" {
		updates["name"] = body.Name
	}
	if body.RW != nil {
		rw := strings.ToLower(strings.TrimSpace(*body.RW))
		if rw != "" && rw != "read" && rw != "write" {
			c.JSON(400, gin.H{"error": "rw must be read|write"})
			return
		}
		updates["rw"] = rw
	}
	if body.NeedData != nil {
		updates["need_data"] = *body.NeedData
	}
	if body.Material != nil && len(*body.Material) > 0 {
		if body.NeedData != nil && !*body.NeedData {
			// 未勾数据级也允许预配声明（不强制）
		}
		if err := validateMaterialDecl(*body.Material); err != nil {
			c.JSON(400, gin.H{"error": "material: " + err.Error()})
			return
		}
		updates["material"] = *body.Material
	} else if body.Material != nil {
		updates["material"] = model.JSONMap(nil) // 显式清空
	}
	if body.ScopeParam != nil {
		if err := validateScopeParam(*body.ScopeParam); err != nil {
			c.JSON(400, gin.H{"error": "scope_param: " + err.Error()})
			return
		}
		updates["scope_param"] = *body.ScopeParam
	}
	if len(updates) == 0 {
		c.JSON(400, gin.H{"error": "nothing to update"})
		return
	}
	if err := d.DB.Model(&model.Action{}).Where("id = ?", rid).Updates(updates).Error; err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	v, _ := d.Access.BumpRouteVersion(appID, "manual", "五格登记更新 "+a.Code, d.currentUserID(c))
	a2, _ := d.Access.ActionByID(rid)
	c.JSON(200, gin.H{"action": a2, "version": v})
}

// validateMaterialDecl 取材声明三选一校验（§3.7；体检门禁②的配置页前置）
//   - id_path   {mode, path}：id 取值路径（path.id / body.instance_id / body.ids[*]）
//   - envelope  {mode, field_path}：信封字段路径（创建类，默认 .meta.account）
//   - fetch_source {mode, url, bind, pick}：补救档回源——占位符必须有绑定、来源五选一
func validateMaterialDecl(m model.JSONMap) error {
	if m == nil {
		return fmt.Errorf("need_data 勾选时必填")
	}
	mode, _ := m["mode"].(string)
	switch mode {
	case "id_path":
		if p, _ := m["path"].(string); strings.TrimSpace(p) == "" {
			return fmt.Errorf("id_path 模式必填 path（如 body.instance_id / path.id）")
		}
	case "envelope":
		fp, _ := m["field_path"].(string)
		if strings.TrimSpace(fp) == "" {
			m["field_path"] = ".meta.account" // 信封规范默认预填（§3.7）
		} else if !strings.HasPrefix(fp, ".") {
			return fmt.Errorf("field_path 须为点号路径（如 .meta.account）")
		}
	case "fetch_source":
		if u, _ := m["url"].(string); strings.TrimSpace(u) == "" {
			return fmt.Errorf("fetch_source 必填 url")
		}
		pick, _ := m["pick"].(string)
		if strings.TrimSpace(pick) == "" {
			return fmt.Errorf("fetch_source 必填 pick（验条件的字段）")
		}
		bind, ok := m["bind"].(map[string]any)
		if !ok || len(bind) == 0 {
			return fmt.Errorf("fetch_source 必填 bind（回源参数绑定字典）")
		}
		for key, v := range bind {
			b, ok := v.(map[string]any)
			if !ok {
				return fmt.Errorf("bind.%s 须为 {from, key|value} 对", key)
			}
			from, _ := b["from"].(string)
			switch from {
			case "path", "query", "body":
				if kv, _ := b["key"].(string); strings.TrimSpace(kv) == "" {
					return fmt.Errorf("bind.%s.from=%s 须给 key", key, from)
				}
			case "const":
				if _, ok := b["value"]; !ok {
					return fmt.Errorf("bind.%s.from=const 须给 value", key)
				}
			case "ctx":
				// 身份上下文变量（$user/$org/$group/$account），key 可省
			default:
				return fmt.Errorf("bind.%s.from=%q 非法（五种来源：path/query/body/const/ctx）", key, from)
			}
		}
	default:
		return fmt.Errorf("mode 必须是 id_path|envelope|fetch_source")
	}
	return nil
}

// validateScopeParam list 动作范围参数格（§3.7；判定两步的契约登记位，§5.2）
func validateScopeParam(s model.JSONMap) error {
	if s == nil {
		return nil // 清空合法
	}
	p, _ := s["param"].(string)
	if strings.TrimSpace(p) == "" {
		return fmt.Errorf("param 必填（如 account）")
	}
	loc, _ := s["location"].(string)
	if loc == "" {
		s["location"] = "query" // 规范：查询过滤条件放 query（§5.2）；历史头=兼容通道
	} else if loc != "query" && loc != "header" {
		return fmt.Errorf("location 必须是 query|header（header=历史兼容通道）")
	}
	return nil
}

// migrateRouteCode 变更阻断 + 一键迁移（§3.9 词表规矩 3）
// 无引用 → 直接迁；有引用且未 confirm → 409 + 受影响清单；confirm=true → 迁移 + 留记录 + 失效策略快照
func (d *Deps) migrateRouteCode(c *gin.Context) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	rid, _ := strconv.ParseUint(c.Param("rid"), 10, 64)
	a, err := d.Access.ActionByID(rid)
	if err != nil || a.AppID != appID {
		c.JSON(404, gin.H{"error": "route not found"})
		return
	}
	var body struct {
		NewCode string `json:"new_code"`
		Confirm bool   `json:"confirm"`
	}
	if err := c.ShouldBindJSON(&body); err != nil || strings.TrimSpace(body.NewCode) == "" {
		c.JSON(400, gin.H{"error": "new_code required"})
		return
	}
	newCode := strings.TrimSpace(body.NewCode)
	if newCode == a.Code {
		c.JSON(400, gin.H{"error": "new_code equals current"})
		return
	}
	refs, _ := d.Access.ActionReferences(rid)
	if !refs.Empty() && !body.Confirm {
		c.JSON(409, gin.H{
			"error": "code_change_blocked", "affected": refs,
			"hint": "语义等价的改名才迁移；确认后带 confirm=true 一键迁移（批量替换引用语义 + 留迁移记录）",
		})
		return
	}
	uid := d.currentUserID(c)
	a2, logRow, err := d.Access.MigrateActionCode(rid, newCode, uid)
	if err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}
	// 策略快照里动作码是构建期烘焙的 → 迁移必须失效缓存
	_ = d.Builder.Bump(c.Request.Context(), appID)
	v, _ := d.Access.BumpRouteVersion(appID, "migrate",
		fmt.Sprintf("%s → %s", logRow.OldCode, logRow.NewCode), uid)
	c.JSON(200, gin.H{"action": a2, "migration": logRow, "version": v})
}

// archiveRoute 归档不删（可查不可用）：被引用 → 拒并列引用方（§3.9）
func (d *Deps) archiveRoute(c *gin.Context) {
	d.setRouteArchived(c, model.StatusArchived)
}

// restoreRoute 恢复归档
func (d *Deps) restoreRoute(c *gin.Context) {
	d.setRouteArchived(c, model.StatusActive)
}

func (d *Deps) setRouteArchived(c *gin.Context, status string) {
	appID, _ := strconv.ParseUint(c.Param("id"), 10, 64)
	rid, _ := strconv.ParseUint(c.Param("rid"), 10, 64)
	a, err := d.Access.ActionByID(rid)
	if err != nil || a.AppID != appID {
		c.JSON(404, gin.H{"error": "route not found"})
		return
	}
	if status == model.StatusArchived {
		refs, _ := d.Access.ActionReferences(rid)
		if !refs.Empty() {
			c.JSON(409, gin.H{"error": "archive_blocked", "affected": refs,
				"hint": "还有包/策略在引用——先解除引用再归档（归档=可查不可用，不删）"})
			return
		}
	}
	if err := d.Access.SetActionStatus(rid, status); err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	_ = d.Builder.Bump(c.Request.Context(), appID) // 归档动作从策略快照剔除
	note := "归档 " + a.Code
	if status == model.StatusActive {
		note = "恢复 " + a.Code
	}
	v, _ := d.Access.BumpRouteVersion(appID, status, note, d.currentUserID(c))
	c.JSON(200, gin.H{"ok": true, "status": status, "version": v})
}
