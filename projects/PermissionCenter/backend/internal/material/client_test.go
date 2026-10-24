package material

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
)

// 路径模板提取：具名槽 / {id} 兜底 / 参数槽兜底 / 段数不匹配
func TestExtractPathParam(t *testing.T) {
	cases := []struct {
		tmpl, actual, name, want string
		ok                       bool
	}{
		{"/disks/{id}", "/disks/d-500", "id", "d-500", true},
		{"/disks/{id}", "/disks/d-500", "", "d-500", true},
		{"/hosts/{hostId}/nics/{nicId}", "/hosts/h-1/nics/n-2", "nicId", "n-2", true},
		{"/hosts/{hostId}/nics/{nicId}", "/hosts/h-1/nics/n-2", "id", "h-1", true}, // 无具名 id → 现行为取首个参数槽
		{"/disks/list", "/disks/list", "id", "", false},                            // 无参数槽
		{"/disks/{id}", "/disks/a/b", "id", "", false},                             // 段数不等
	}
	for _, c := range cases {
		got, ok := ExtractPathParam(c.tmpl, c.actual, c.name)
		if got != c.want || ok != c.ok {
			t.Errorf("ExtractPathParam(%q,%q,%q) = (%q,%v)，want (%q,%v)",
				c.tmpl, c.actual, c.name, got, ok, c.want, c.ok)
		}
	}
}

// 点号/下标取值：信封字段与嵌套路径
func TestNested(t *testing.T) {
	m := map[string]any{
		"meta":  map[string]any{"account": 123, "region": "cn-hz"},
		"items": []any{map[string]any{"account": 456}, map[string]any{"account": 789}},
		"spec":  map[string]any{"instance_id": "i-999"},
	}
	cases := []struct {
		path string
		want any
		ok   bool
	}{
		{".meta.account", 123, true},
		{"meta.region", "cn-hz", true},
		{"items[1].account", 789, true},
		{"spec.instance_id", "i-999", true},
		{".meta.missing", nil, false},
		{"meta.account.x", nil, false},
		{"items[9].account", nil, false},
		{"", nil, false},
	}
	for _, c := range cases {
		got, ok := Nested(m, c.path)
		if ok != c.ok {
			t.Errorf("Nested(%q) ok=%v，want %v", c.path, ok, c.ok)
			continue
		}
		if ok && got != c.want {
			t.Errorf("Nested(%q) = %v，want %v", c.path, got, c.want)
		}
	}
}

// 信封叶子键：条件字段名
func TestLeafKey(t *testing.T) {
	if got := LeafKey(".meta.account"); got != "account" {
		t.Errorf("LeafKey(.meta.account) = %q", got)
	}
	if got := LeafKey("items[0].account"); got != "account" {
		t.Errorf("LeafKey(items[0].account) = %q", got)
	}
}

// 点查客户端三态：200 拿行 / 404=ErrNotFound / 500=ErrUnavailable / 未配置地址=ErrUnavailable
func TestFetchRow三态(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Perm-Query-Token") != "tok-1" {
			w.WriteHeader(401)
			return
		}
		switch {
		case r.URL.Path == "/ok":
			w.Write([]byte(`{"row":{"account":123,"type":"ssd"}}`))
		case r.URL.Path == "/missing":
			w.WriteHeader(404)
		default:
			w.WriteHeader(500)
		}
	}))
	defer srv.Close()
	c := NewClient()
	ctx := context.Background()

	row, err := c.FetchRow(ctx, srv.URL+"/ok", "tok-1", "disk", "disk-1")
	if err != nil || row["account"] != float64(123) {
		t.Fatalf("200 路径: row=%v err=%v", row, err)
	}
	_, err = c.FetchRow(ctx, srv.URL+"/missing", "tok-1", "disk", "disk-x")
	if !errors.Is(err, ErrNotFound) {
		t.Errorf("404 应为 ErrNotFound，got %v", err)
	}
	_, err = c.FetchRow(ctx, srv.URL+"/boom", "tok-1", "disk", "disk-1")
	if !errors.Is(err, ErrUnavailable) {
		t.Errorf("500 应为 ErrUnavailable（fail-closed），got %v", err)
	}
	_, err = c.FetchRow(ctx, srv.URL+"/ok", "wrong", "disk", "disk-1")
	if !errors.Is(err, ErrUnavailable) {
		t.Errorf("凭证不符应 ErrUnavailable，got %v", err)
	}
	_, err = c.FetchRow(ctx, "", "", "disk", "disk-1")
	if !errors.Is(err, ErrUnavailable) {
		t.Errorf("未配置回查地址应 ErrUnavailable，got %v", err)
	}
}

// 补救档绑定字典：五来源 + 缺参 fail-closed
func TestResolveBind(t *testing.T) {
	body := map[string]any{"meta": map[string]any{"owner": "u1"}, "ids": []any{"a", "b"}}
	froms := map[string]map[string]any{
		"path":  {"disk_id": "d-500"},
		"query": {"region": "cn-hz"},
		"ctx":   {"account": "123"},
	}
	bind := map[string]any{
		"disk_id": map[string]any{"from": "path", "key": "disk_id"},
		"region":  map[string]any{"from": "query", "key": "region"},
		"owner":   map[string]any{"from": "body", "key": "meta.owner"},
		"tenant":  map[string]any{"from": "const", "value": "t-1"},
		"account": map[string]any{"from": "ctx", "key": "account"},
	}
	got, err := ResolveBind(bind, body, froms)
	if err != nil {
		t.Fatalf("ResolveBind: %v", err)
	}
	if got["disk_id"] != "d-500" || got["region"] != "cn-hz" || got["owner"] != "u1" ||
		got["tenant"] != "t-1" || got["account"] != "123" {
		t.Errorf("五来源解参: %v", got)
	}
	// 缺参 → fail-closed
	_, err = ResolveBind(map[string]any{"x": map[string]any{"from": "body", "key": "nope"}}, body, froms)
	if err == nil {
		t.Error("body 取值不存在应报错（fail-closed）")
	}
	_, err = ResolveBind(map[string]any{"x": map[string]any{"from": "evil", "key": "k"}}, body, froms)
	if err == nil {
		t.Error("非法来源应报错")
	}
}

// 回源 URL 模板替换
func TestSubstURL(t *testing.T) {
	got := SubstURL("GET /api/v1/disks/{disk_id}", map[string]any{"disk_id": "d-500"})
	if got != "GET /api/v1/disks/d-500" {
		t.Errorf("SubstURL = %q", got)
	}
}
