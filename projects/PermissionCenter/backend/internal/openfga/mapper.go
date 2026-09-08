package openfga

// ModelDefs 授权模型：user/service/group 主体 + host/network/disk 资源
// 可分配关系在 metadata.directly_related_user_types 声明（OpenFGA v1.8 校验要求）
// reader/writer 允许直接主体（user/service）与组主体（group#member）
func ModelDefs() []TypeDef {
	assignable := []map[string]any{
		{"type": "user"},
		{"type": "service"},
		{"type": "group", "relation": "member"},
	}
	relDef := func() map[string]map[string]any {
		return map[string]map[string]any{
			"owner":  {"this": map[string]any{}},
			"reader": {"this": map[string]any{}},
			"writer": {"this": map[string]any{}},
		}
	}
	metaDef := func() map[string]any {
		return map[string]any{
			"relations": map[string]any{
				"owner":  map[string]any{"directly_related_user_types": assignable},
				"reader": map[string]any{"directly_related_user_types": assignable},
				"writer": map[string]any{"directly_related_user_types": assignable},
			},
		}
	}
	// TypeDef 目前没有 Metadata 字段——用内联扩展结构（见 TypeDefWithMeta）
	return []TypeDef{
		{Type: "user", Relations: map[string]map[string]any{}},
		{Type: "service", Relations: map[string]map[string]any{}},
		{
			Type:      "group",
			Relations: map[string]map[string]any{"member": {"this": map[string]any{}}},
			Metadata:  map[string]any{"relations": map[string]any{"member": map[string]any{"directly_related_user_types": []map[string]any{{"type": "user"}}}}},
		},
		{Type: "host", Relations: relDef(), Metadata: metaDef()},
		{Type: "network", Relations: relDef(), Metadata: metaDef()},
		{Type: "disk", Relations: relDef(), Metadata: metaDef()},
	}
}

// OpToRelation 操作 → OpenFGA 关系
func OpToRelation(op string) string {
	switch op {
	case "read":
		return "reader"
	default: // create / update / delete
		return "writer"
	}
}
