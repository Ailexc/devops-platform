package onboard

import (
	"testing"

	"github.com/xcy/permission-center/internal/model"
)

func app() *model.App {
	return &model.App{Code: "cmdb", Name: "CMDB"}
}

func act(code, method, path, resource, operation string) model.Action {
	return model.Action{Code: code, Method: method, Path: path,
		Resource: resource, Operation: operation, Status: model.StatusActive}
}

// 六种坏配置各被阻断并列明原因（T4 验收项）
func TestSixBadConfigsBlocked(t *testing.T) {
	contracts := map[string]model.DataContract{
		"disk": {ModelCode: "disk", Fields: []string{"type", "size_gb"}},
	}
	clients := map[string]model.Client{
		"good-cli": {ClientID: "good-cli", Status: model.StatusEnabled},
	}

	// ① 缺动作（推断不出）
	r := Run(app(), nil, []model.RoutePending{
		{Method: "POST", Path: "/api/v1/disks/{id}", Status: model.PendPending, Reason: "⑤兜底：POST 带路径参数且末段非动作词"},
	}, contracts, clients)
	assertBlocked(t, r, "NO_ACTION")

	// ② 格式错（非全小写三段）
	r = Run(app(), []model.Action{act("Cmdb:Host:Read", "GET", "/api/v1/hosts/{id}", "host", "read")}, nil, contracts, clients)
	assertBlocked(t, r, "BAD_FORMAT")

	// ③ 重复（同路由挂多码）
	r = Run(app(), []model.Action{
		act("cmdb:host:read", "GET", "/api/v1/hosts/{id}", "host", "read"),
		act("cmdb:host:get", "GET", "/api/v1/hosts/{id}", "host", "get"),
	}, nil, contracts, clients)
	assertBlocked(t, r, "DUP_ROUTE")

	// ④a 勾数据级缺取材声明
	a := act("cmdb:disk:update", "PATCH", "/api/v1/disks/{id}", "disk", "update")
	a.NeedData = true
	r = Run(app(), []model.Action{a}, nil, contracts, clients)
	assertBlocked(t, r, "MATERIAL_MISSING")

	// ④b 回源占位符无绑定 + pick 不在 schema
	a = act("cmdb:disk:update", "PATCH", "/api/v1/disks/{id}", "disk", "update")
	a.NeedData = true
	a.Material = model.JSONMap{"mode": "fetch_source",
		"url": "GET /api/v1/disks/{disk_id}", "pick": "account",
		"bind": map[string]any{"disk_id": map[string]any{"from": "body"}}}
	r = Run(app(), []model.Action{a}, nil, contracts, clients)
	assertBlocked(t, r, "PICK_NOT_IN_SCHEMA") // pick=account 不在契约 fields=[type,size_gb]

	a.Material["pick"] = "type"
	a.Material["bind"] = map[string]any{} // 占位符 disk_id 无绑定
	r = Run(app(), []model.Action{a}, nil, contracts, clients)
	assertBlocked(t, r, "PLACEHOLDER_UNBOUND")

	// ④c 裸豁免（只配路径未绑凭证）
	ap := app()
	ap.ExemptPaths = model.JSONMap{"/api/v1/health": ""}
	r = Run(ap, nil, nil, contracts, clients)
	assertBlocked(t, r, "BARE_EXEMPT")

	// ④d 数据级 create 缺范围字段路径
	a = act("cmdb:disk:create", "POST", "/api/v1/disks", "disk", "create")
	a.NeedData = true
	a.Material = model.JSONMap{"mode": "envelope"}
	r = Run(app(), []model.Action{a}, nil, contracts, clients)
	assertBlocked(t, r, "CREATE_NO_SCOPE_PATH")

	// ⑤ 导入一致性（资源段与路径模板不符）
	r = Run(app(), []model.Action{act("cmdb:disk:edit", "PATCH", "/api/v1/volumes/{id}", "disk", "update")},
		nil, contracts, clients)
	assertBlocked(t, r, "RESOURCE_MISMATCH")
}

// 正常导入报告全绿（ready）
func TestHealthyReady(t *testing.T) {
	contracts := map[string]model.DataContract{
		"host": {ModelCode: "host", Fields: []string{"name", "owner_id"}},
	}
	clients := map[string]model.Client{"cli": {ClientID: "cli", Status: model.StatusEnabled}}

	read := act("cmdb:host:read", "GET", "/api/v1/hosts/{id}", "host", "read")
	read.NeedData = true
	read.Material = model.JSONMap{"mode": "id_path", "path": "path.id"}
	create := act("cmdb:host:create", "POST", "/api/v1/hosts", "host", "create")
	create.NeedData = true
	create.Material = model.JSONMap{"mode": "envelope", "field_path": ".meta.account"}
	list := act("cmdb:host:list", "GET", "/api/v1/hosts", "host", "list")
	list.ScopeParam = model.JSONMap{"param": "env", "location": "query", "required": true}

	ap := app()
	ap.ExemptPaths = model.JSONMap{"/api/v1/health": "cli"}
	r := Run(ap, []model.Action{read, create, list}, nil, contracts, clients)
	if r.Status != "ready" || len(r.Blocked) != 0 || len(r.Warnings) != 0 {
		t.Fatalf("期望 ready 全绿，实得 status=%s blocked=%v warnings=%v", r.Status, r.Blocked, r.Warnings)
	}
	if r.Actions != 3 || r.Registered != 3 {
		t.Fatalf("路由计数错：actions=%d registered=%d", r.Actions, r.Registered)
	}
}

// 未确认路由停"未完成"态（warn 不阻断）+ 归档不参与体检
func TestIncompleteAndArchived(t *testing.T) {
	archived := act("cmdb:host:old", "GET", "/api/v1/hosts/{id}", "host", "read")
	archived.Status = model.StatusArchived
	r := Run(app(), []model.Action{archived}, []model.RoutePending{
		{Method: "GET", Path: "/api/v1/e2e-things", InferredCode: "cmdb:e2e-thing:list",
			Status: model.PendPending, Reason: "④形态表：GET 集合路径 → list"},
	}, nil, nil)
	if r.Status != "incomplete" {
		t.Fatalf("期望 incomplete，实得 %s", r.Status)
	}
	if r.Actions != 0 {
		t.Fatalf("归档动作不应计入 active：%d", r.Actions)
	}
	if len(r.Warnings) != 1 || r.Warnings[0].Code != "PENDING_UNCONFIRMED" {
		t.Fatalf("期望 PENDING_UNCONFIRMED warn，实得 %v", r.Warnings)
	}
}

// 别名路由显式登记=合法（同码多路由的例外不阻断）
func TestAliasRouteLegal(t *testing.T) {
	a := act("cmdb:host:read", "GET", "/api/v1/hosts/{id}", "host", "read")
	a.AliasRoutes = model.StringArray{"GET /api/v2/hosts/{id}"}
	r := Run(app(), []model.Action{a}, nil, nil, nil)
	if r.Status != "ready" {
		t.Fatalf("显式别名路由不应阻断：%v", r.Blocked)
	}
}

// 豁免绑定有效凭证=合法
func TestExemptWithValidClient(t *testing.T) {
	ap := app()
	ap.ExemptPaths = model.JSONMap{"/api/v1/health": "cli"}
	r := Run(ap, nil, nil, nil, map[string]model.Client{
		"cli": {ClientID: "cli", Status: model.StatusEnabled},
	})
	if r.Status != "ready" {
		t.Fatalf("绑定有效凭证的豁免不应阻断：%v", r.Blocked)
	}
	// 凭证禁用=自锁 → 阻断
	r = Run(ap, nil, nil, nil, map[string]model.Client{
		"cli": {ClientID: "cli", Status: 0},
	})
	assertBlocked(t, r, "BARE_EXEMPT")
}

func assertBlocked(t *testing.T, r Report, code string) {
	t.Helper()
	for _, b := range r.Blocked {
		if b.Code == code {
			if b.Reason == "" {
				t.Fatalf("%s 阻断必须列明原因", code)
			}
			return
		}
	}
	t.Fatalf("期望阻断 %s，实得 blocked=%v status=%s", code, r.Blocked, r.Status)
}
