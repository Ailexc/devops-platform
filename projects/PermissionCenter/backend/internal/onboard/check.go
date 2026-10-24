// Package onboard 接入体检（方案 §3.9，T4）：应用注册/导入/发版重新导入时自动跑，报告回执。
//
// 只做硬的五类（能强制的绝不靠自觉；检测不是治理——起名好坏、同义词一律不管）：
//
//	① 缺动作：待确认队列中推断不出动作码（POST 带 id 等存量不规范）→ 阻断
//	② 格式错：动作码非全小写三段 app:resource:verb → 阻断
//	③ 重复：同路由挂多码 → 阻断（同码多路由的例外=显式"别名路由"登记，§3.9 L5 口径）
//	④ 配置自洽：勾数据级缺取材声明 / 回源占位符无绑定 / pick 不在回源 schema（契约 fields）
//	           / 裸豁免（豁免路径未绑有效 M2M 凭证——自锁或裸奔）/ 数据级 create 缺范围字段路径 → 阻断
//	⑤ 导入一致性：三段码资源段与路径模板不符（disk:edit 挂 /volumes）→ 阻断
//
//	⑤'（warn 级）推断预填未人工确认 → 接入停在"未完成"态（不是阻断，是状态）。
//
// 纯函数引擎：输入全部显式传入，DB 加载归 api handler——单测可构造任意坏配置。
package onboard

import (
	"fmt"
	"strings"

	"github.com/xcy/permission-center/internal/model"
)

// Finding 一条体检发现
type Finding struct {
	Level  string `json:"level"` // block|warn
	Code   string `json:"code"`  // NO_ACTION|BAD_FORMAT|DUP_ROUTE|MATERIAL_MISSING|PLACEHOLDER_UNBOUND|PICK_NOT_IN_SCHEMA|BARE_EXEMPT|CREATE_NO_SCOPE_PATH|RESOURCE_MISMATCH|PENDING_UNCONFIRMED
	Method string `json:"method,omitempty"`
	Path   string `json:"path,omitempty"`
	Action string `json:"action,omitempty"`
	Reason string `json:"reason"`
}

// Report 接入体检报告（§3.9 报告回执）
type Report struct {
	AppCode    string    `json:"app_code"`
	Actions    int       `json:"actions"`             // active 路由总数
	Registered int       `json:"registered"`          // 已登记动作码数（= actions，路由表本体即动作行）
	Blocked    []Finding `json:"blocked"`             // 阻断：不修完不能接入
	Warnings   []Finding `json:"warnings"`            // 待确认：接入停在"未完成"态
	Pending    int       `json:"pending_unconfirmed"` // 推断预填未人工确认条数
	Status     string    `json:"status"`              // ready|incomplete|blocked
}

// Run 跑五类硬校验。
//
//	customers：app 绑定的 M2M 凭证（client_id → Client）——裸豁免检查用（§3.1 豁免主语=M2M 凭证）
//	contracts：数据域契约（model_code → DataContract）——pick 不在回源 schema 检查用
func Run(app *model.App, acts []model.Action, pendings []model.RoutePending,
	contracts map[string]model.DataContract, clients map[string]model.Client) Report {

	rep := Report{AppCode: app.Code}
	blocks, warns := []Finding{}, []Finding{}

	// ---- 过滤 active（归档=可查不可用，不参与体检） ----
	active := make([]model.Action, 0, len(acts))
	for _, a := range acts {
		if a.Status != model.StatusArchived {
			active = append(active, a)
		}
	}
	rep.Actions = len(active)
	rep.Registered = len(active) // 路由表本体=动作行，每行必有码

	// ---- ② 格式错（全小写三段） ----
	for _, a := range active {
		if err := model.ValidateCodeFormat(a.Code); err != nil {
			blocks = append(blocks, Finding{
				Level: "block", Code: "BAD_FORMAT",
				Method: a.Method, Path: a.Path, Action: a.Code,
				Reason: "动作码格式错（非全小写三段）：" + err.Error(),
			})
		}
	}

	// ---- ③ 重复：同路由挂多码（主路由+别名路由合并统计；别名=显式登记的合法例外） ----
	routeCodes := map[string]map[string]bool{} // "METHOD path" → {code}
	for _, a := range active {
		addRoute(routeCodes, a.Method, a.Path, a.Code)
		for _, al := range a.AliasRoutes {
			m, p := splitAlias(al)
			if m != "" {
				addRoute(routeCodes, m, p, a.Code)
			}
		}
	}
	for rk, codes := range routeCodes {
		if len(codes) > 1 {
			parts := strings.SplitN(rk, " ", 2)
			list := make([]string, 0, len(codes))
			for c := range codes {
				list = append(list, c)
			}
			blocks = append(blocks, Finding{
				Level: "block", Code: "DUP_ROUTE",
				Method: parts[0], Path: parts[1],
				Reason: fmt.Sprintf("同一路由挂多码（%s）——归档旧码或改走迁移", strings.Join(list, "、")),
			})
		}
	}

	// ---- ④ 配置自洽（逐动作） ----
	for _, a := range active {
		// 勾数据级（need_data）→ 取材声明★必填
		if a.NeedData && (a.Material == nil || strOf(a.Material, "mode") == "") {
			blocks = append(blocks, Finding{
				Level: "block", Code: "MATERIAL_MISSING",
				Method: a.Method, Path: a.Path, Action: a.Code,
				Reason: "勾了数据级但没配取材声明（id 路径/信封字段路径/补救回源 三选一）",
			})
		}
		if a.Material != nil {
			switch strOf(a.Material, "mode") {
			case "fetch_source":
				blocks = append(blocks, checkFetchSource(a, contracts)...)
			case "envelope":
				// 数据级 create：取材声明②即【范围字段路径】（创建越权检查用，§3.7）
				if a.Operation == "create" && strOf(a.Material, "field_path") == "" {
					blocks = append(blocks, Finding{
						Level: "block", Code: "CREATE_NO_SCOPE_PATH",
						Method: a.Method, Path: a.Path, Action: a.Code,
						Reason: "create 缺范围字段路径（不填=中心不知道去 body 哪拿账号=无法防越权）",
					})
				}
			}
		}

		// ---- ⑤ 导入一致性：资源段 vs 路径模板（通用路由跳过——资源在运行期由槽位/X-Resource-Type 解析） ----
		if !a.IsGeneric && a.Resource != "" && a.Resource != "*" {
			if !resourceInPath(a.Resource, a.Path) {
				blocks = append(blocks, Finding{
					Level: "block", Code: "RESOURCE_MISMATCH",
					Method: a.Method, Path: a.Path, Action: a.Code,
					Reason: fmt.Sprintf("三段码资源段 %q 与路径模板不符（路径静态段中找不到该资源）", a.Resource),
				})
			}
		}
	}

	// ---- ④ 裸豁免：豁免路径未绑有效 M2M 凭证（§3.1 豁免主语=凭证不是路由；自锁或裸奔） ----
	for path, raw := range app.ExemptPaths {
		clientID, _ := raw.(string)
		if clientID == "" {
			blocks = append(blocks, Finding{
				Level: "block", Code: "BARE_EXEMPT", Path: path,
				Reason: "裸豁免：豁免只配路径未绑中心 M2M 凭证（自锁或裸奔）",
			})
			continue
		}
		cli, ok := clients[clientID]
		if !ok || cli.Status != model.StatusEnabled {
			blocks = append(blocks, Finding{
				Level: "block", Code: "BARE_EXEMPT", Path: path,
				Reason: fmt.Sprintf("豁免绑定的 M2M 凭证 %q 不存在或已禁用（自锁或裸奔）", clientID),
			})
		}
	}

	// ---- ① 缺动作（推断不出）+ ⑤' 推断预填未人工确认 → 停"未完成"态 ----
	pendingN := 0
	for _, p := range pendings {
		if p.Status != model.PendPending {
			continue
		}
		if p.InferredCode == "" {
			blocks = append(blocks, Finding{
				Level: "block", Code: "NO_ACTION",
				Method: p.Method, Path: p.Path,
				Reason: "无动作码且推断不出（" + p.Reason + "）——存量不规范，人工登记五格",
			})
			continue
		}
		pendingN++
		warns = append(warns, Finding{
			Level: "warn", Code: "PENDING_UNCONFIRMED",
			Method: p.Method, Path: p.Path, Action: p.InferredCode,
			Reason: "推断预填未人工确认（" + p.Reason + "）→ 接入停在『未完成』状态",
		})
	}
	rep.Pending = pendingN
	rep.Blocked = blocks
	rep.Warnings = warns

	switch {
	case len(blocks) > 0:
		rep.Status = "blocked"
	case pendingN > 0:
		rep.Status = "incomplete"
	default:
		rep.Status = "ready"
	}
	return rep
}

// checkFetchSource 补救回源自洽：占位符全绑定 + pick 在回源 schema（= 数据契约 fields，判定字段白名单）
func checkFetchSource(a model.Action, contracts map[string]model.DataContract) []Finding {
	var out []Finding
	url := strOf(a.Material, "url")
	bind, _ := a.Material["bind"].(map[string]any)

	// 占位符 {xxx} 必须有绑定（§3.7 三条规则之一：缺=配置页不让存）
	for _, ph := range placeholders(url) {
		if _, ok := bind[ph]; !ok {
			out = append(out, Finding{
				Level: "block", Code: "PLACEHOLDER_UNBOUND",
				Method: a.Method, Path: a.Path, Action: a.Code,
				Reason: fmt.Sprintf("回源占位符 {%s} 无绑定（绑定字典缺该键）", ph),
			})
		}
	}

	// pick 必须在回源 schema——契约 fields=判定字段白名单（"判定字段=落库字段"钉死精神）
	pick := strOf(a.Material, "pick")
	if pick == "" {
		out = append(out, Finding{
			Level: "block", Code: "PICK_NOT_IN_SCHEMA",
			Method: a.Method, Path: a.Path, Action: a.Code,
			Reason: "回源缺 pick（验条件字段）",
		})
	} else if c, ok := contracts[a.Resource]; !ok {
		out = append(out, Finding{
			Level: "block", Code: "PICK_NOT_IN_SCHEMA",
			Method: a.Method, Path: a.Path, Action: a.Code,
			Reason: fmt.Sprintf("回源域 %q 未登记数据契约——pick 无 schema 可校验", a.Resource),
		})
	} else if !containsFold(c.Fields, pick) {
		out = append(out, Finding{
			Level: "block", Code: "PICK_NOT_IN_SCHEMA",
			Method: a.Method, Path: a.Path, Action: a.Code,
			Reason: fmt.Sprintf("pick %q 不在回源 schema（数据契约 fields=%v）", pick, c.Fields),
		})
	}
	return out
}

// resourceInPath 资源段与路径模板一致：任一静态段与资源段互为前缀（容忍复数化 hosts/host、databases/database）。
// 不当保姆：同义词（volume vs disk）不管——业务方自己的事（§3.9 检测不是治理）。
func resourceInPath(resource, path string) bool {
	for _, seg := range strings.Split(strings.Trim(path, "/"), "/") {
		if seg == "" || strings.HasPrefix(seg, "{") || isVersionSeg(seg) {
			continue
		}
		if seg == resource || strings.HasPrefix(seg, resource) || strings.HasPrefix(resource, seg) {
			return true
		}
	}
	return false
}

func isVersionSeg(s string) bool {
	return len(s) > 1 && s[0] == 'v' && s[1] >= '0' && s[1] <= '9'
}

// placeholders 提取 url 中的 {xxx} 占位符
func placeholders(url string) []string {
	var out []string
	for i := 0; i < len(url); i++ {
		if url[i] != '{' {
			continue
		}
		if j := strings.IndexByte(url[i:], '}'); j > 1 {
			out = append(out, url[i+1:i+j])
			i += j
		}
	}
	return out
}

// splitAlias 别名路由条目 "METHOD /path" → method, path
func splitAlias(s string) (string, string) {
	parts := strings.SplitN(strings.TrimSpace(s), " ", 2)
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		return "", ""
	}
	return strings.ToUpper(parts[0]), parts[1]
}

func addRoute(m map[string]map[string]bool, method, path, code string) {
	rk := strings.ToUpper(method) + " " + path
	if m[rk] == nil {
		m[rk] = map[string]bool{}
	}
	m[rk][code] = true
}

func strOf(m model.JSONMap, k string) string {
	s, _ := m[k].(string)
	return s
}

func containsFold(list []string, want string) bool {
	for _, s := range list {
		if strings.EqualFold(s, want) {
			return true
		}
	}
	return false
}
