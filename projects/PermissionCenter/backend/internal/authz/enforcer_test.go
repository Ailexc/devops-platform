package authz

import "testing"

// TestEnforcerExactAction 权限点 code 含 ":"，必须精确匹配（keyMatch2 会把 : 当通配，此处回归）
func TestEnforcerExactAction(t *testing.T) {
	en, err := NewEnforcer()
	if err != nil {
		t.Fatal(err)
	}
	// 策略：u:1 拥有 cmdb:host:read
	if err := en.Reset(
		[][]string{{"u:1", "cmdb", "cmdb:host:read", "*", "allow", "p1"}},
		[][]string{},
	); err != nil {
		t.Fatal(err)
	}
	if ok, _ := en.Check("u:1", "cmdb", "cmdb:host:read", "*"); !ok {
		t.Error("read should allow")
	}
	// create/update/delete 不应误匹配 read
	for _, act := range []string{"cmdb:host:create", "cmdb:host:update", "cmdb:host:delete", "cmdb:network:read"} {
		if ok, _ := en.Check("u:1", "cmdb", act, "*"); ok {
			t.Errorf("action %s should NOT match cmdb:host:read", act)
		}
	}
}

// TestEnforcerGroup 组嵌套（g:child → g:parent → policy）
func TestEnforcerGroup(t *testing.T) {
	en, _ := NewEnforcer()
	en.Reset(
		[][]string{{"g:10", "cmdb", "cmdb:host:create", "*", "allow", "p1"}},
		[][]string{
			{"u:1", "g:10"},  // 用户属于组
			{"g:10", "g:20"}, // 组嵌套
		},
	)
	// u:1 → g:10 → 直接授予
	if ok, _ := en.Check("u:1", "cmdb", "cmdb:host:create", "*"); !ok {
		t.Error("user in group should allow")
	}
}

// TestMatchPids 命中策略 ID（数据级授权复用）
func TestMatchPids(t *testing.T) {
	en, _ := NewEnforcer()
	ps := &PolicySet{
		Groupings: [][]string{{"u:1", "g:10"}},
		Policies: [][]string{
			{"u:1", "cmdb", "cmdb:host:read", "*", "allow", "1"},
			{"u:1", "cmdb", "cmdb:host:create", "*", "allow", "2"},
			{"g:10", "cmdb", "cmdb:host:update", "*", "allow", "3"},
			{"u:9", "cmdb", "cmdb:host:read", "*", "allow", "4"},
		},
	}
	closure := en.ResolveClosure("u:1", ps.Groupings)
	got := matchPidsForTest(ps, closure, "cmdb", "cmdb:host:read")
	if len(got) != 1 || got[0] != "1" {
		t.Errorf("expected [1], got %v", got)
	}
	got = matchPidsForTest(ps, closure, "cmdb", "cmdb:host:update")
	if len(got) != 1 || got[0] != "3" {
		t.Errorf("expected [3], got %v", got)
	}
}

func matchPidsForTest(ps *PolicySet, closure []string, app, action string) []string {
	in := map[string]bool{}
	for _, s := range closure {
		in[s] = true
	}
	var pids []string
	for _, row := range ps.Policies {
		if row[4] != "allow" || !in[row[0]] || row[1] != app {
			continue
		}
		if row[2] != "*" && row[2] != action {
			continue
		}
		pids = append(pids, row[5])
	}
	return pids
}
