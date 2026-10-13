package store

import (
	"testing"

	"github.com/xcy/permission-center/internal/model"
)

// T1 §3.8 specificity 钉死：静态段数多者优先 → 同数逐段从左比（静态>参数）→ 全等按登记序
func TestMoreSpecific(t *testing.T) {
	a := func(id uint64, path string) model.Action {
		act := model.Action{Path: path}
		act.ID = id
		return act
	}
	cases := []struct {
		name       string
		x, y       model.Action
		wantXFirst bool
	}{
		{"静态段数多者优先", a(1, "/disks/list"), a(2, "/disks/{id}"), true},
		{"静态段数多者优先_反序输入", a(2, "/disks/{id}"), a(1, "/disks/list"), false},
		{"同数逐段从左比_静态赢", a(1, "/disks/{id}/meta"), a(2, "/disks/health/{x}"), false},
		{"同数逐段从左比_左静态优先", a(1, "/a/static/{x}"), a(2, "/a/{x}/static"), true},
		{"全等按登记序", a(3, "/disks/{id}"), a(7, "/disks/{id}"), true},
		{"全等登记序_反", a(7, "/disks/{id}"), a(3, "/disks/{id}"), false},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := moreSpecific(c.x, c.y); got != c.wantXFirst {
				t.Errorf("moreSpecific(%s#%d, %s#%d) = %v, want %v",
					c.x.Path, c.x.ID, c.y.Path, c.y.ID, got, c.wantXFirst)
			}
		})
	}
}

// 排序后 matchPath 命中优先级：/disks/{id}（3 静态）必须先于 /disks/list 之外的参数泛匹配
// ——典型撞车：字面 /disks/list 与模板 /disks/{id} 都能命中 GET /disks/list？不能（list 是静态），
// 真正撞车：模板 /disks/{id} vs 更具体的 /disks/health（静态 2 vs 3）
func TestSpecificity排序后命中(t *testing.T) {
	cands := []model.Action{
		a2(1, "/disks/{id}"),
		a2(2, "/disks/health"),
		a2(3, "/disks/{id}/snapshots"),
	}
	// 模拟 ResolveActionSteps 的排序
	for i := 0; i < len(cands); i++ {
		for j := i + 1; j < len(cands); j++ {
			if moreSpecific(cands[j], cands[i]) {
				cands[i], cands[j] = cands[j], cands[i]
			}
		}
	}
	// GET /disks/health：/disks/health（静态3）应排最前并被 matchPath 命中
	if !matchPath(cands[0].Path, "/disks/health") || cands[0].ID != 2 {
		t.Errorf("排序后首元素应为 /disks/health（id=2），got %s#%d", cands[0].Path, cands[0].ID)
	}
	// GET /disks/abc/snapshots：/disks/{id}/snapshots 应排在 /disks/{id} 前（静态数 3>2... 实际 4>2）
	if !matchPath(cands[0].Path, "/disks/abc/snapshots") && !matchPath(cands[1].Path, "/disks/abc/snapshots") {
		t.Errorf("排序结果无法命中嵌套路径: %+v", cands)
	}
}

func a2(id uint64, path string) model.Action {
	act := model.Action{Path: path}
	act.ID = id
	return act
}
