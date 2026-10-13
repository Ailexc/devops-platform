package sync

import "testing"

// T1 §3.8 推断四条+一兜底：判定顺序先③后② + 形态表 + 兜底
func TestInferRoute(t *testing.T) {
	verbs := VerbSet([]string{"reboot"}) // 内置已含 reboot，顺带验证应用词表叠加
	cases := []struct {
		name, method, path string
		op, rw, resource   string
		pending            bool
		confident          bool
	}{
		// ③ 业务动作：POST + 末段 ∈ 词表（先于②，不会被抢成 create）
		{"post动词_路径带id", "POST", "/api/v1/instances/{id}/reboot", "reboot", "write", "instance", true, true},
		{"post动词_无id", "POST", "/api/v1/instances/reboot", "reboot", "write", "instance", true, true},
		{"post动词_自定义词", "POST", "/api/v1/secrets/rotate", "rotate", "write", "secret", true, true},
		// ② create：POST 集合路径、无参数段、末段 ∉ 词表
		{"create集合", "POST", "/api/v1/disks", "create", "write", "disk", true, true},
		{"create嵌套集合", "POST", "/api/v1/projects/123/secrets", "create", "write", "secret", true, true},
		// ⑤ POST 带 id 但末段非词 → 人工档
		{"post带id非词", "POST", "/api/v1/instances/{id}", "", "", "", true, false},
		// ④ GET 形态表（不认动作段）
		{"get集合", "GET", "/api/v1/disks", "list", "read", "disk", true, true},
		{"get单个", "GET", "/api/v1/disks/{id}", "get", "read", "disk", true, true},
		{"get静态后缀", "GET", "/api/v1/disks/status", "", "", "", true, false},
		// ④ 写方法尾参数
		{"patch编辑", "PATCH", "/api/v1/disks/{id}", "edit", "write", "disk", true, true},
		{"delete单个", "DELETE", "/api/v1/disks/{id}", "delete", "write", "disk", true, true},
		// ⑤ 兜底
		{"delete集合", "DELETE", "/api/v1/disks", "", "", "", true, false},
		{"put非词尾段", "PUT", "/api/v1/disks/flush-all", "", "", "", true, false},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			got := InferRoute(c.method, c.path, verbs)
			if !got.Pending {
				t.Errorf("推断结果必须恒 Pending=true（预填永不直接生效），got=%v", got.Pending)
			}
			if got.Operation != c.op || got.RW != c.rw || got.Resource != c.resource || got.Confident != c.confident {
				t.Errorf("InferRoute(%s %s) = {op:%q rw:%q res:%q confident:%v}，want {op:%q rw:%q res:%q confident:%v}（reason=%s）",
					c.method, c.path, got.Operation, got.RW, got.Resource, got.Confident,
					c.op, c.rw, c.resource, c.confident, got.Reason)
			}
		})
	}
}

// 词表叠加：应用登记动词生效；集合段不被误当动词
func TestVerbSet叠加(t *testing.T) {
	verbs := VerbSet([]string{"Explode", " start "}) // 大小写归一 + 去空 + 内置 start 重复
	if !verbs["explode"] {
		t.Error("应用登记动词应小写归一进词表")
	}
	if !verbs["reboot"] || !verbs["start"] {
		t.Error("内置词表应在")
	}
	got := InferRoute("POST", "/api/v1/hosts/explode", verbs)
	if got.Operation != "explode" || got.Resource != "host" {
		t.Errorf("自定义动词推断失败: %+v", got)
	}
	// disks 不是动词 → create
	got2 := InferRoute("POST", "/api/v1/disks", verbs)
	if got2.Operation != "create" {
		t.Errorf("集合段不应被当动词: %+v", got2)
	}
}
