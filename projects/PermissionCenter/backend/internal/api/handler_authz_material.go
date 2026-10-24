package api

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xcy/permission-center/internal/authz"
	"github.com/xcy/permission-center/internal/material"
)

// handleCheckMaterial T2 带体调用（方案 §5.1）——创建 / 存量 body-id / fetch_source 的供材通道。
// 业务持有请求体，把材料带到判定点（fetch-and-bring 落地）：Demo Traefik 不带体时的 body 材料通道，
// 与网关链路（path 材料）同一套判定契约。
//
// 供材合同（PEP 共享密钥）：
//
//	POST /v1/authz/check-material
//	{ "user", "app", "action", "material": {…原始请求体或信封…},
//	  "path"?: "/api/v1/…", "query"?: {…}, "trace_id"?: "…" }
//
// 取材按登记的取材声明分发（§3.7）：
//   - id_path  body.*   → 抠 id → 点查权威行 → 范围谓词（存量 POST body-id 主路）
//   - id_path  path.*   → 需带 path（或直接走网关链路，网关自持 URI）
//   - envelope .meta.x  → 信封即"未来的行"（取不到=403 MATERIAL_MISSING，fail-closed）
//   - fetch_source      → 绑定字典解参（body/const/ctx/path/query）→ 回源取行
//   - 未勾数据级        → 仅动作级
func (d *Deps) handleCheckMaterial(c *gin.Context) {
	var req struct {
		User     string         `json:"user"`
		App      string         `json:"app"`
		Action   string         `json:"action"`
		Material map[string]any `json:"material"`
		Path     string         `json:"path"`
		Query    map[string]any `json:"query"`
		TraceID  string         `json:"trace_id"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.User == "" || req.App == "" || req.Action == "" {
		c.JSON(400, gin.H{"error": "user/app/action required"})
		return
	}
	app, err := d.Apps.ByCode(req.App)
	if err != nil {
		c.JSON(403, gin.H{"decision": "deny", "code": "APP_NOT_FOUND", "message": "unknown app"})
		return
	}
	// deny-by-default：动作码未登记 → 拒（运行期纯查表，§3.8）
	act, err := d.Access.ActionByCode(app.ID, req.Action)
	if err != nil {
		c.JSON(403, gin.H{"decision": "deny", "code": "NO_ACTION", "message": "action not registered"})
		return
	}

	pep := map[string]any{"channel": "check-material", "method": req.Action}
	if act.NeedData && len(act.Material) > 0 {
		pep["decl"] = act.Material
	}

	// 1) 动作级（Casbin 短路）
	dec, matchedPids, err := d.Checker.CheckWithPids(c.Request.Context(), authz.CheckRequest{
		User: req.User, App: req.App, Action: req.Action,
		TraceID: req.TraceID, PEP: pep,
	})
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	if !dec.Allow {
		d.logDecision(req.TraceID, req.User, app, req.Action, req.App+":"+req.Action, false, "action denied", pep)
		c.JSON(403, gin.H{"decision": "deny", "code": dec.Code, "message": dec.Reason})
		return
	}

	// 2) 数据级（取材声明分发）
	if !act.NeedData || len(act.Material) == 0 {
		d.logDecision(req.TraceID, req.User, app, req.Action, req.App+":"+req.Action, true, "action only", pep)
		c.JSON(200, gin.H{"decision": "allow"})
		return
	}

	mode, _ := act.Material["mode"].(string)
	var row map[string]any
	externalID := ""
	denyCode, denyMsg := "", ""

	switch mode {
	case "id_path":
		decl, _ := act.Material["path"].(string)
		switch {
		case strings.HasPrefix(decl, "body."):
			v, ok := material.Nested(req.Material, strings.TrimPrefix(decl, "body."))
			if !ok {
				denyCode, denyMsg = "MATERIAL_MISSING", "id 取值路径在材料中不存在（fail-closed）"
				break
			}
			externalID = fmt.Sprintf("%v", v)
		case strings.HasPrefix(decl, "path."):
			if req.Path == "" {
				c.JSON(400, gin.H{"error": "path.* 声明的判定由网关链路完成——请走 forwardAuth 或请求带 path"})
				return
			}
			id, ok := material.ExtractPathParam(act.Path, req.Path, strings.TrimPrefix(decl, "path."))
			if !ok {
				denyCode, denyMsg = "MATERIAL_MISSING", "路径模板提取不出 id（fail-closed）"
				break
			}
			externalID = id
		default:
			c.JSON(400, gin.H{"error": "id_path 声明须为 path.* 或 body.*"})
			return
		}
		if denyCode == "" {
			// 模型白名单：只允许已登记数据契约的域（§3.1 防"查任意表"）
			if _, cerr := d.Contracts.ByModelCode(act.Resource); cerr != nil {
				denyCode, denyMsg = "MODEL_NOT_REGISTERED", "数据域未登记数据契约（白名单外）"
			} else {
				row, err = d.Mat.FetchRow(c.Request.Context(), app.PermQueryURL, app.PermQueryToken, act.Resource, externalID)
				switch {
				case err == nil:
				case errors.Is(err, material.ErrNotFound):
					denyCode, denyMsg = "DATA_MISSING", "权威行不存在（fail-closed）"
				default:
					denyCode, denyMsg = "DATA_SOURCE_UNAVAILABLE", "点查失败："+err.Error()+"（fail-closed，无隐式降级）"
				}
			}
		}

	case "envelope":
		fp, _ := act.Material["field_path"].(string)
		if fp == "" {
			fp = ".meta.account"
		}
		v, ok := material.Nested(req.Material, fp)
		if !ok {
			denyCode, denyMsg = "MATERIAL_MISSING", "信封字段不存在（fail-closed——请求即未来的行，缺字段无法防越权）"
			break
		}
		// 判定字段=落库字段（契约测试钉死）；伪行 = {叶子键: 值}——伪造被授权集封顶（§3.7 防伪边界）
		row = map[string]any{material.LeafKey(fp): v}
		pep["envelope_field"] = fp

	case "fetch_source":
		urlT, _ := act.Material["url"].(string)
		bindRaw, _ := act.Material["bind"].(map[string]any)
		froms := map[string]map[string]any{
			"ctx":   {"user": req.User, "app": req.App},
			"query": req.Query,
		}
		if req.Path != "" {
			// path 来源：按动作模板逐绑定键具名提取（§3.7 五来源——from: path）
			pathVals := map[string]any{}
			for k, raw := range bindRaw {
				if b, ok := raw.(map[string]any); ok {
					if from, _ := b["from"].(string); from == "path" {
						if key, _ := b["key"].(string); key != "" {
							if v, ok := material.ExtractPathParam(act.Path, req.Path, key); ok {
								pathVals[key] = v
							}
						}
					}
				}
				_ = k
			}
			froms["path"] = pathVals
		}
		bound, berr := material.ResolveBind(bindRaw, req.Material, froms)
		if berr != nil {
			denyCode, denyMsg = "MATERIAL_BIND_FAILED", "回源绑定解参失败："+berr.Error()
			break
		}
		method, fullURL, uerr := material.ResolveFetchURL(urlT, app.PermQueryURL)
		if uerr != nil {
			denyCode, denyMsg = "MATERIAL_DECL_INVALID", uerr.Error()
			break
		}
		row, err = d.Mat.FetchAny(c.Request.Context(), method, material.SubstURL(fullURL, bound), app.PermQueryToken)
		switch {
		case err == nil:
			pep["fetch_source"] = fullURL
		case errors.Is(err, material.ErrNotFound):
			denyCode, denyMsg = "DATA_MISSING", "回源无该行（fail-closed）"
		default:
			denyCode, denyMsg = "DATA_SOURCE_UNAVAILABLE", "回源失败："+err.Error()
		}

	default:
		c.JSON(400, gin.H{"error": "取材声明 mode 必须是 id_path|envelope|fetch_source"})
		return
	}

	// 3) 范围谓词求值（权威行/伪行 × 各域策略）
	if denyCode == "" {
		allow, reason, cerr := d.DataPlane.CheckRow(subjectOFGAKey(req.User), act.Resource, externalID, row, matchedPids)
		if cerr != nil {
			d.logDecision(req.TraceID, req.User, app, req.Action, act.Resource+":"+externalID, false, "data engine: "+cerr.Error(), pep)
			c.JSON(503, gin.H{"decision": "deny", "code": "DATA_ENGINE_UNAVAILABLE", "message": cerr.Error()})
			return
		}
		if !allow {
			if reason == "data_missing" {
				denyCode, denyMsg = "DATA_MISSING", "权威行不存在（fail-closed）"
			} else {
				denyCode, denyMsg = "NO_PERMISSION", "范围谓词不匹配"
			}
		} else {
			pep["row_fields"] = len(row)
			d.logDecision(req.TraceID, req.User, app, req.Action, act.Resource+":"+externalID, true, "material check", pep)
			c.JSON(200, gin.H{"decision": "allow"})
			return
		}
	}

	d.logDecision(req.TraceID, req.User, app, req.Action, act.Resource+":"+externalID, false, denyMsg, pep)
	c.JSON(403, gin.H{"decision": "deny", "code": denyCode, "message": denyMsg, "ts": time.Now().Unix()})
}
