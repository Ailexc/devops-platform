package api

import "testing"

// T6 场景参数联动（§4.2 升级一）：$key 引用解析 / shared 防错位钉子 / 参数缺失
func TestApplyScenarioParam(t *testing.T) {
	linkedPreset := map[string]any{
		"param_linkage": "shared",
		"scenario_params": []any{
			map[string]any{"key": "account", "label": "云账号", "type": "select"},
		},
	}
	indepPreset := map[string]any{"param_linkage": "independent"}
	params := map[string]any{"account": "acc-ops-001"}

	// ① $key 引用 → 解析并回写（一次选定全域同值）
	sel := map[string]any{"model": "host", "type": "select", "selectedValue": "$account"}
	if err := applyScenarioParam(linkedPreset, sel, "account", "host", params); err != nil {
		t.Fatalf("引用解析不应报错：%v", err)
	}
	if sel["selectedValue"] != "acc-ops-001" {
		t.Fatalf("解析值错：%v", sel["selectedValue"])
	}

	// ② shared + field 命中参数 key + 字面值 → 拒（防域间错位的服务端钉子）
	sel = map[string]any{"model": "disk", "type": "select", "selectedValue": "acc-rd-002"}
	err := applyScenarioParam(linkedPreset, sel, "account", "disk", params)
	if err == nil {
		t.Fatal("shared 联动字面值应被拒（错位防护）")
	}

	// ③ shared + 字面值但 field 不在参数 key → 放行（真独立的域允许独立选）
	sel = map[string]any{"model": "host", "type": "select", "selectedValue": "prod"}
	if err := applyScenarioParam(linkedPreset, sel, "env", "host", params); err != nil {
		t.Fatalf("非参数域不应受限：%v", err)
	}

	// ④ 引用了未提供的参数 → 拒（fail-closed）
	sel = map[string]any{"model": "host", "type": "select", "selectedValue": "$missing"}
	if err := applyScenarioParam(linkedPreset, sel, "account", "host", params); err == nil {
		t.Fatal("缺失参数应报错")
	}

	// ⑤ 独立模式：字面值放行、引用仍解析（引用是合法表达，独立模式不禁止）
	sel = map[string]any{"model": "host", "type": "select", "selectedValue": "prod"}
	if err := applyScenarioParam(indepPreset, sel, "account", "host", params); err != nil {
		t.Fatalf("独立模式字面值不应报错：%v", err)
	}
	sel = map[string]any{"model": "host", "type": "select", "selectedValue": "$account"}
	if err := applyScenarioParam(indepPreset, sel, "account", "host", params); err != nil ||
		sel["selectedValue"] != "acc-ops-001" {
		t.Fatalf("独立模式引用仍应解析：%v %v", err, sel["selectedValue"])
	}

	// ⑥ multi_select 值数组逐项解析
	sel = map[string]any{"model": "host", "type": "multi_select", "selectedValues": []any{"$account", "static-1"}} // JSON 反序列化形态
	if err := applyScenarioParam(linkedPreset, sel, "account_id", "host", params); err != nil {
		t.Fatalf("multi_select 解析不应报错：%v", err)
	}
	vs := anyStrings(sel["selectedValues"])
	if len(vs) != 2 || vs[0] != "acc-ops-001" || vs[1] != "static-1" {
		t.Fatalf("multi_select 解析错：%v", vs)
	}
}

// T6 validatePresetLinkage：层级树引用域⊆data_models / 每域至多一父 / 联动枚举
func TestValidatePresetLinkage(t *testing.T) {
	base := func() map[string]any {
		return map[string]any{"data_models": []any{"host", "disk", "nic"}}
	}
	// 合法：树 host→disk→nic
	p := base()
	p["data_model_tree"] = []any{map[string]any{
		"model":    "host",
		"children": []any{map[string]any{"model": "disk", "children": []any{map[string]any{"model": "nic"}}}},
	}}
	p["param_linkage"] = "shared"
	p["scenario_params"] = []any{map[string]any{"key": "account", "type": "select"}}
	if err := validatePresetLinkage(0, p); err != nil {
		t.Fatalf("合法配置不应报错：%v", err)
	}

	// 树引用了 data_models 外的域 → 拒
	p = base()
	p["data_model_tree"] = []any{map[string]any{"model": "volume"}}
	if err := validatePresetLinkage(0, p); err == nil {
		t.Fatal("树引用域外应拒")
	}

	// 同域两父（菱形）→ 拒
	p = base()
	p["data_model_tree"] = []any{
		map[string]any{"model": "host", "children": []any{map[string]any{"model": "disk"}}},
		map[string]any{"model": "nic", "children": []any{map[string]any{"model": "disk"}}},
	}
	if err := validatePresetLinkage(0, p); err == nil {
		t.Fatal("同域两父应拒")
	}

	// 非法联动枚举 → 拒
	p = base()
	p["param_linkage"] = "locked"
	if err := validatePresetLinkage(0, p); err == nil {
		t.Fatal("非法 param_linkage 应拒")
	}

	// 参数 key 重复 → 拒
	p = base()
	p["scenario_params"] = []any{
		map[string]any{"key": "account"}, map[string]any{"key": "account"},
	}
	if err := validatePresetLinkage(0, p); err == nil {
		t.Fatal("重复参数 key 应拒")
	}
}
