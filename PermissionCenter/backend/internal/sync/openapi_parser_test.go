package sync

import "testing"

// TestParseOpenAPI P2 验收：OpenAPI → 规范化权限点（12 个：host/network/disk × CRUD）
func TestParseOpenAPI(t *testing.T) {
	raw := []byte(`{
		"openapi": "3.0.0",
		"info": {"title": "CMDB API", "version": "1.0.0"},
		"paths": {
			"/api/v1/hosts": {
				"get":  {"tags": ["主机管理"], "summary": "主机列表"},
				"post": {"tags": ["主机管理"], "summary": "创建主机"}
			},
			"/api/v1/hosts/{id}": {
				"get":    {"tags": ["主机管理"], "summary": "主机详情"},
				"patch":  {"tags": ["主机管理"], "summary": "更新主机"},
				"delete": {"tags": ["主机管理"], "summary": "删除主机"}
			},
			"/api/v1/networks/{id}": {
				"get": {"tags": ["网络管理"], "summary": "网络详情"}
			}
		}
	}`)
	actions, err := ParseOpenAPI(raw, "cmdb")
	if err != nil {
		t.Fatal(err)
	}
	// 期望：host(5) + network(1) = 6 个
	if len(actions) != 6 {
		t.Fatalf("expected 6 actions, got %d", len(actions))
	}
	// 复数归一化：hosts → host；路径参数段忽略
	has := map[string]bool{}
	for _, a := range actions {
		has[a.Code] = true
	}
	for _, want := range []string{"cmdb:host:list", "cmdb:host:read", "cmdb:host:create", "cmdb:host:update", "cmdb:host:delete", "cmdb:network:read"} {
		if !has[want] {
			t.Errorf("missing action %s; got %v", want, has)
		}
	}
}

// TestResourceFromPath 复数归一化
func TestResourceFromPath(t *testing.T) {
	cases := map[string]string{
		"/api/v1/hosts":          "host",
		"/api/v1/hosts/{id}":     "host",
		"/api/v1/networks":       "network",
		"/api/v1/disks/{id}":     "disk",
	}
	for path, want := range cases {
		if got := resourceFromPath(path); got != want {
			t.Errorf("resourceFromPath(%s) = %s, want %s", path, got, want)
		}
	}
}

// TestParseOpenAPIGeneric 阶段 9：通用接口解析（路径模板 + 统一查询入口）
func TestParseOpenAPIGeneric(t *testing.T) {
	raw := []byte(`{
		"openapi": "3.0.0",
		"info": {"title": "CMDB API", "version": "1.0.0"},
		"paths": {
			"/api/v1/{model}": {
				"get":  {"summary": "按资源类型查询列表"},
				"post": {"summary": "按资源类型创建"}
			},
			"/api/v1/{model}/{id}": {
				"get":    {"summary": "按资源类型查详情"},
				"patch":  {"summary": "按资源类型更新"},
				"delete": {"summary": "按资源类型删除"}
			},
			"/api/v1/entities": {
				"get": {"summary": "统一查询"}
			}
		}
	}`)
	actions, err := ParseOpenAPI(raw, "cmdb")
	if err != nil {
		t.Fatal(err)
	}
	if len(actions) != 6 {
		t.Fatalf("expected 6 generic actions, got %d", len(actions))
	}
	byCode := map[string]ParsedAction{}
	for _, a := range actions {
		if !a.IsGeneric {
			t.Errorf("action %s should be generic", a.Code)
		}
		byCode[a.Code] = a
	}
	// 集合 GET → list；详情 GET → read；POST → create；PATCH → update；DELETE → delete
	expect := map[string]string{
		"cmdb:model:list":   "model",
		"cmdb:model:create": "model",
		"cmdb:model:read":   "model",
		"cmdb:model:update": "model",
		"cmdb:model:delete": "model",
		"cmdb:entities:list": "header",
	}
	for code, slot := range expect {
		a, ok := byCode[code]
		if !ok {
			t.Errorf("missing generic action %s; got %v", code, byCode)
			continue
		}
		if a.ResourceSlot != slot {
			t.Errorf("%s ResourceSlot = %s, want %s", code, a.ResourceSlot, slot)
		}
	}
}

// TestGenericSlot 通用路由检测
func TestGenericSlot(t *testing.T) {
	cases := []struct {
		path     string
		slot     string
		kind     string
		ok       bool
	}{
		{"/api/v1/{model}", "model", "collection", true},
		{"/api/v1/{model}/{id}", "model", "detail", true},
		{"/api/v1/hosts", "", "", false},
		{"/api/v1/hosts/{id}", "", "", false},
		{"/api/v2/{resource}/items/{id}", "", "", false},
	}
	for _, c := range cases {
		slot, kind, ok := genericSlot(c.path)
		if ok != c.ok || slot != c.slot || kind != c.kind {
			t.Errorf("genericSlot(%s) = (%s,%s,%v), want (%s,%s,%v)", c.path, slot, kind, ok, c.slot, c.kind, c.ok)
		}
	}
}
