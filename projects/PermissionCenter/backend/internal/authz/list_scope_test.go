package authz

import (
	"testing"

	"github.com/xcy/permission-center/internal/model"
)

func pol(scope model.JSONMap) model.Policy {
	return model.Policy{Status: model.PolicyActive, ResourceScope: scope}
}

// T5 §5.2 元组集合语义：nil=全量 / 条件在本维=值并集 / 条件在别维=本维不受限 / 集合式不覆盖列表维
func TestScopeValuesOf(t *testing.T) {
	cases := []struct {
		name     string
		ps       []model.Policy
		param    string
		wantFull bool
		wantVals map[string]bool
	}{
		{"nil scope=全量", []model.Policy{pol(nil)}, "env", true, nil},
		{"条件在本维=单值", []model.Policy{
			pol(model.JSONMap{"model": "host", "condition": map[string]any{"op": "eq", "field": "env", "value": "prod"}}),
		}, "env", false, map[string]bool{"prod": true}},
		{"条件在别维=本维不受限", []model.Policy{
			pol(model.JSONMap{"model": "host", "condition": map[string]any{"op": "eq", "field": "ip", "value": "10.0.0.1"}}),
		}, "env", true, nil},
		{"跨策略：值并集", []model.Policy{
			pol(model.JSONMap{"model": "host", "condition": map[string]any{"op": "eq", "field": "env", "value": "prod"}}),
			pol(model.JSONMap{"model": "host", "condition": map[string]any{"op": "eq", "field": "env", "value": "test"}}),
		}, "env", false, map[string]bool{"prod": true, "test": true}},
		{"跨策略：一条全量即全量", []model.Policy{
			pol(model.JSONMap{"model": "host", "condition": map[string]any{"op": "eq", "field": "env", "value": "prod"}}),
			pol(nil),
		}, "env", true, nil},
		{"他域策略不覆盖", []model.Policy{
			pol(model.JSONMap{"model": "disk", "condition": map[string]any{"op": "eq", "field": "env", "value": "prod"}}),
		}, "env", false, map[string]bool{}},
		{"集合式不覆盖列表维", []model.Policy{
			pol(model.JSONMap{"model": "host", "instance_ids": []any{float64(1)}}),
		}, "env", false, map[string]bool{}},
		{"dimension 式=多值", []model.Policy{
			pol(model.JSONMap{"model": "host", "dimension": "env", "values": []any{"prod", "dev"}}),
		}, "env", false, map[string]bool{"prod": true, "dev": true}},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			full, vals := ScopeValuesOf(c.ps, "host", c.param)
			if full != c.wantFull {
				t.Errorf("full=%v want %v", full, c.wantFull)
			}
			if !c.wantFull {
				if len(vals) != len(c.wantVals) {
					t.Fatalf("vals=%v want %v", vals, c.wantVals)
				}
				for k := range c.wantVals {
					if !vals[k] {
						t.Errorf("缺值 %q（got %v）", k, vals)
					}
				}
			}
		})
	}
}

// T5 子集校验：全部在集内=过；首个越权值返回；无授权全拒
func TestSubsetCheck(t *testing.T) {
	if v, ok := SubsetCheck([]string{"prod"}, false, map[string]bool{"prod": true}); !ok || v != "" {
		t.Errorf("在集内应过: %q %v", v, ok)
	}
	if v, ok := SubsetCheck([]string{"prod", "dev"}, false, map[string]bool{"prod": true}); ok || v != "dev" {
		t.Errorf("越权值应返回: %q %v", v, ok)
	}
	if v, ok := SubsetCheck([]string{"prod"}, true, nil); !ok || v != "" {
		t.Errorf("full 应放行: %q %v", v, ok)
	}
	if v, ok := SubsetCheck([]string{"x"}, false, map[string]bool{}); ok || v != "x" {
		t.Errorf("无授权应全拒: %q %v", v, ok)
	}
}

func TestParseScopeParamList(t *testing.T) {
	got := ParseScopeParamList("prod, test ,,dev")
	if len(got) != 3 || got[0] != "prod" || got[2] != "dev" {
		t.Errorf("解析 %v", got)
	}
	if len(ParseScopeParamList("")) != 0 {
		t.Error("空串应为空集")
	}
}
