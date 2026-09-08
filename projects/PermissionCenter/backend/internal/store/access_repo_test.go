package store

import (
	"testing"

	"github.com/xcy/permission-center/internal/model"
)

// TestResolveGenericResource 阶段 9：通用路由资源解析（路径槽位 + X-Resource-Type 兜底）
func TestResolveGenericResource(t *testing.T) {
	cases := []struct {
		name       string
		action     *model.Action
		path       string
		header     string
		wantRes    string
		wantOK     bool
	}{
		{
			name:    "路径槽位解析",
			action:  &model.Action{Path: "/api/v1/{model}", ResourceSlot: "model"},
			path:    "/api/v1/hosts",
			wantRes: "host",
			wantOK:  true,
		},
		{
			name:    "路径槽位复数归一化",
			action:  &model.Action{Path: "/api/v1/{model}", ResourceSlot: "model"},
			path:    "/api/v1/networks",
			wantRes: "network",
			wantOK:  true,
		},
		{
			name:    "详情路径",
			action:  &model.Action{Path: "/api/v1/{model}/{id}", ResourceSlot: "model"},
			path:    "/api/v1/disks/3",
			wantRes: "disk",
			wantOK:  true,
		},
		{
			name:    "X-Resource-Type 兜底",
			action:  &model.Action{Path: "/api/v1/entities", ResourceSlot: "header"},
			path:    "/api/v1/entities",
			header:  "host",
			wantRes: "host",
			wantOK:  true,
		},
		{
			name:    "无 header 且无槽位 → 失败（写操作拒绝）",
			action:  &model.Action{Path: "/api/v1/entities", ResourceSlot: "header"},
			path:    "/api/v1/entities",
			wantRes: "",
			wantOK:  false,
		},
		{
			name:    "路径结构不匹配 → 失败",
			action:  &model.Action{Path: "/api/v1/{model}/{id}", ResourceSlot: "model"},
			path:    "/api/v1/hosts",
			wantRes: "",
			wantOK:  false,
		},
	}
	for _, c := range cases {
		res, ok := resolveGenericResource(c.action, c.path, c.header)
		if ok != c.wantOK || res != c.wantRes {
			t.Errorf("%s: resolveGenericResource() = (%s,%v), want (%s,%v)",
				c.name, res, ok, c.wantRes, c.wantOK)
		}
	}
}

// TestSlotValueFromPath 槽位值提取
func TestSlotValueFromPath(t *testing.T) {
	val, ok := slotValueFromPath("/api/v1/{model}", "/api/v1/hosts")
	if !ok || val != "hosts" {
		t.Errorf("slotValueFromPath = (%s,%v), want (hosts,true)", val, ok)
	}
	_, ok = slotValueFromPath("/api/v1/{model}", "/api/v1/hosts/3")
	if ok {
		t.Error("expected structural mismatch to fail")
	}
}
