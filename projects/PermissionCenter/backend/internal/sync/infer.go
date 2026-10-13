package sync

import (
	"fmt"
	"strings"
)

// v1.5 T1 导入推断（方案 §3.8）：四条 + 一兜底，判定顺序写死【先③业务动作、后②create】。
// 推断永远不活在运行期——仅导入时预填，预填永不直接生效（Pending=true），人工确认后落表。

// BuiltinVerbs 平台内置通用动作词表（动作段候选；应用可登记动词追加）
var BuiltinVerbs = map[string]bool{
	"reboot": true, "start": true, "stop": true, "restart": true, "resize": true,
	"renew": true, "migrate": true, "scale": true, "deploy": true, "rollback": true,
	"pause": true, "resume": true, "reset": true, "bind": true, "unbind": true,
	"attach": true, "detach": true, "snapshot": true, "restore": true, "flush": true,
	"rotate": true, "disable": true, "enable": true, "promote": true, "demote": true,
}

// VerbSet 词表 = 内置 + 应用已登记动作段（导入时可编辑，§3.8 判定顺序③的依据）
func VerbSet(appVerbs []string) map[string]bool {
	out := make(map[string]bool, len(BuiltinVerbs)+len(appVerbs))
	for v := range BuiltinVerbs {
		out[v] = true
	}
	for _, v := range appVerbs {
		v = strings.ToLower(strings.TrimSpace(v))
		if v != "" {
			out[v] = true
		}
	}
	return out
}

// Inferred 推断结果（恒 Pending=true：预填永不直接生效）
type Inferred struct {
	Operation string `json:"operation"` // list|get|create|edit|delete|<verb>
	RW        string `json:"rw"`        // read|write
	Resource  string `json:"resource"`  // 资源段（单数）
	Verb      string `json:"verb"`      // 动作段（create/list/get/edit/delete/自定义动词）
	Pending   bool   `json:"pending"`   // 恒 true（人工确认后落表）
	Reason    string `json:"reason"`    // 推断依据 / 推不出原因
	Confident bool   `json:"confident"` // 形态表确定（list/get/edit/delete/create 词）vs 动词推断
}

// InferRoute 推断一条路由的动作码要素。
// appCode 用于产出完整动作码 InferredCode(app:resource:verb)——调用方拼。
// 判定顺序（§3.8 写死）：
//
//	③ 业务动作：写方法 + 末段 ∉ 参数段 + 末段 ∈ 词表 → 动作段=该词（POST /instances/reboot ✓）
//	② create   ：POST 集合路径（无参数段）且 末段 ∉ 词表 → create
//	④ 形态表   ：GET 集合=list / GET 带尾参数=get / PATCH|PUT {id}=edit / DELETE {id}=delete
//	⑤ 兜底     ：推不出唯一结果 → 调用方进待确认队列（不猜）
func InferRoute(method, path string, verbs map[string]bool) Inferred {
	method = strings.ToUpper(method)
	segs := nonEmptySegs(path)
	if len(segs) == 0 {
		return Inferred{Pending: true, Reason: "空路径，推不出"}
	}
	last := segs[len(segs)-1]
	lastIsParam := strings.HasPrefix(last, "{")
	resource := inferResource(segs, verbs)

	switch method {
	case "POST":
		// ③ 业务动作先判——POST /instances/reboot 不会被②抢成 create
		if !lastIsParam && verbs[last] {
			return Inferred{
				Operation: last, RW: "write", Resource: resource, Verb: last,
				Pending: true, Confident: true,
				Reason: fmt.Sprintf("③业务动作：POST + 末段 %q ∈ 动作词表", last),
			}
		}
		// ② create：POST 集合路径（无任何参数段）且末段 ∉ 词表
		if !hasParamSeg(segs) {
			return Inferred{
				Operation: "create", RW: "write", Resource: resource, Verb: "create",
				Pending: true, Confident: true,
				Reason: "②create：POST 集合路径且末段 ∉ 词表",
			}
		}
		return Inferred{
			Pending: true,
			Reason:  "⑤兜底：POST 带路径参数且末段非动作词——存量不规范，走人工档",
		}
	case "GET":
		// GET 一律不认动作段（§3.8 ④）：读动作只有 list/get，形态表直接给
		if lastIsParam {
			return Inferred{Operation: "get", RW: "read", Resource: resource, Verb: "get",
				Pending: true, Confident: true, Reason: "④形态表：GET 尾参数 → get"}
		}
		if !hasExtraStaticSuffix(segs) {
			return Inferred{Operation: "list", RW: "read", Resource: resource, Verb: "list",
				Pending: true, Confident: true, Reason: "④形态表：GET 集合路径 → list"}
		}
		return Inferred{Pending: true, Reason: "⑤兜底：GET 带多余静态段，形态表无此格（如 /disks/status）"}
	case "PUT", "PATCH":
		if lastIsParam {
			return Inferred{Operation: "edit", RW: "write", Resource: resource, Verb: "edit",
				Pending: true, Confident: true, Reason: "④形态表：写方法 + 尾参数 → edit"}
		}
		if verbs[last] {
			return Inferred{Operation: last, RW: "write", Resource: resource, Verb: last,
				Pending: true, Confident: true,
				Reason: fmt.Sprintf("③业务动作：写方法 + 末段 %q ∈ 动作词表", last),
			}
		}
		return Inferred{Pending: true, Reason: "⑤兜底：写方法尾段非参数且非动作词，推不出唯一结果"}
	case "DELETE":
		if lastIsParam {
			return Inferred{Operation: "delete", RW: "write", Resource: resource, Verb: "delete",
				Pending: true, Confident: true, Reason: "④形态表：DELETE + 尾参数 → delete"}
		}
		return Inferred{Pending: true, Reason: "⑤兜底：DELETE 集合（批量删除）形态表无此格，走人工档"}
	default:
		return Inferred{Pending: true, Reason: "⑤兜底：非 CRUD 方法，推不出"}
	}
}

// nonEmptySegs 去空的路径段
func nonEmptySegs(path string) []string {
	raw := strings.Split(strings.Trim(path, "/"), "/")
	out := make([]string, 0, len(raw))
	for _, s := range raw {
		if s != "" {
			out = append(out, s)
		}
	}
	return out
}

// hasParamSeg 是否含 {param} 段（create 判定用：POST 集合路径不允许带路径参数）
func hasParamSeg(segs []string) bool {
	for _, s := range segs {
		if strings.HasPrefix(s, "{") {
			return true
		}
	}
	return false
}

// hasExtraStaticSuffix GET 集合形态判定：尾段静态且其前一段是版本段（或不存在）→ 集合（list）；
// 否则（前段是普通静态段/参数段）视为多余静态段（如 /disks/status、/disks/{id}/health）→ 兜底
func hasExtraStaticSuffix(segs []string) bool {
	n := len(segs)
	if n == 0 {
		return false
	}
	if strings.HasPrefix(segs[n-1], "{") {
		return false // get 分支已处理
	}
	if n == 1 {
		return false // 裸集合
	}
	prev := segs[n-2]
	return strings.HasPrefix(prev, "{") || !isVersionSegment(prev)
}

// inferResource 资源段：最近的非参数、非版本、非动作词静态段（单数化）
// /api/v1/instances/reboot → instances → instance（不能取 reboot，resourceFromPath 会踩这个坑）
func inferResource(segs []string, verbs map[string]bool) string {
	for i := len(segs) - 1; i >= 0; i-- {
		s := segs[i]
		if s == "" || strings.HasPrefix(s, "{") || isVersionSegment(s) {
			continue
		}
		ls := strings.ToLower(s)
		if verbs[ls] {
			continue // 跳过动作段
		}
		return singularize(ls)
	}
	return ""
}

// OperationRW 按 operation 推导读写 bit（登记 RW 为空时的默认值）
func OperationRW(operation string) string {
	switch strings.ToLower(operation) {
	case "list", "get", "read":
		return "read"
	default:
		return "write"
	}
}
