package main

import (
	"context"
	"fmt"
	"log"
	"sort"
	"strconv"

	"github.com/xcy/permission-center/internal/api"
	"github.com/xcy/permission-center/internal/auth"
	"github.com/xcy/permission-center/internal/config"
	"github.com/xcy/permission-center/internal/model"
	"github.com/xcy/permission-center/internal/store"
	"gorm.io/gorm"
)

// seed 种子数据（Go 程序写入，零 SQL 文件）
// reset=true 时先清空 demo 域表再重建（一键重置初始化，make seed-reset）
func seed(reset bool) error {
	cfg := config.Load()
	db, err := store.Open(cfg.PGDSN)
	if err != nil {
		return err
	}
	if reset {
		if err := resetDemoData(db); err != nil {
			return err
		}
		log.Println("[seed] demo data reset done (TRUNCATE ... RESTART IDENTITY CASCADE)")
	}
	cache, err := store.NewCache(cfg.RedisAddr)
	if err != nil {
		return err
	}
	deps := api.NewDeps(cfg, db, cache)
	ctx := context.Background()

	// （1.5 T3）数据级=点查权威行（material/CheckRow），无需 OpenFGA schema 初始化

	// 1. admin 用户
	adminHash, _ := auth.HashPassword("admin123")
	admin := &model.User{
		Username:     "admin",
		DisplayName:  "管理员",
		Email:        "admin@iam.local",
		PasswordHash: adminHash,
		Status:       model.StatusEnabled,
		Attributes:   map[string]any{"level": "L5"},
		Source:       model.SourceLocal,
	}
	if err := deps.Users.Create(admin); err != nil {
		log.Printf("[seed] admin exists: %v", err)
		admin, _ = deps.Users.ByUsername("admin")
	}

	// 2. 组织树
	root := findOrCreateOrg(deps, "总公司", nil)
	rdCenter := findOrCreateOrg(deps, "研发中心", &root.ID)
	rd1 := findOrCreateOrg(deps, "研发一部", &rdCenter.ID)
	rd2 := findOrCreateOrg(deps, "研发二部", &rdCenter.ID)
	opsCenter := findOrCreateOrg(deps, "运维中心", &root.ID)
	opsPlatform := findOrCreateOrg(deps, "平台运维部", &opsCenter.ID)
	opsApp := findOrCreateOrg(deps, "应用运维部", &opsCenter.ID)

	// 2.1 清理重复组织（历史 seed 残留）
	cleanupDuplicateOrgs(deps)

	// 3. 用户（含演示用户 小黄/小红）
	seedUser(deps, "alice", "爱丽丝", rd1.ID, true)
	seedUser(deps, "bob", "鲍勃", rd1.ID, false)
	seedUser(deps, "erin", "艾琳", opsPlatform.ID, true)
	seedUser(deps, "frank", "弗兰克", opsApp.ID, true)
	// 演示用户：小黄（研发一部，应用 Owner）、小红（研发二部，申请者）
	seedUser(deps, "xiaohuang", "小黄", rd1.ID, false)
	seedUser(deps, "xiaohong", "小红", rd2.ID, false)

	// 4. 应用
	app := seedApp(deps, cfg, "cmdb", "配置管理数据库", admin.ID)
	// 爱丽丝为 cmdb 联合负责人（应用管理里可见"我管理的应用"）
	ensureOwner(deps, app.ID, userID(deps, "alice"), false)
	monitorApp := seedApp(deps, cfg, "monitor", "监控告警中心", userID(deps, "erin"))
	itsmApp := seedApp(deps, cfg, "itsm", "IT服务管理", admin.ID)
	opsToolApp := seedApp(deps, cfg, "ops-tool", "运维工具平台", userID(deps, "frank"))
	// 云管平台（v12 接入申请演示：提供方 + 消费方双角色，erin 为 owner）
	cloudApp := seedApp(deps, cfg, "cloudportal", "云管平台", userID(deps, "erin"))

	// 4.1 应用元数据
	seedAppMeta(deps, app, model.JSONMap{
		"cloud": "自建机房", "account": "-", "region": "cn-east-1",
		"vpc": "vpc-cmdb", "subnet": "subnet-cmdb-1", "sg": "sg-cmdb-prod",
	}, model.JSONAny{
		map[string]any{"icon": "🔑", "name": "OAuth 2.0", "type": "oauth2_client_credentials", "strength": "high", "strengthLabel": "高",
			"desc": "标准 OAuth2 Client Credentials 流程，适合服务间调用"},
	})
	// 应用基础信息（描述/语言/所属组）
	app.Description = "配置管理数据库：统一纳管主机/网络/存储等基础设施资源，对外提供资源全生命周期管理能力"
	app.Language = "Go"
	app.DocURL = "https://docs.example.com/cmdb/manual"
	ogID := rdCenter.ID
	app.OwnerGroupID = &ogID
	deps.Apps.Update(app)

	seedAppMeta(deps, opsToolApp, model.JSONMap{
		"cloud": "自建机房", "account": "-", "region": "cn-east-1",
		"vpc": "vpc-ops", "subnet": "subnet-ops-1", "sg": "sg-ops-prod",
	}, model.JSONAny{
		map[string]any{"icon": "🔑", "name": "API Key", "type": "api_key", "strength": "medium", "strengthLabel": "中",
			"desc": "请求头携带固定 Key，适合工具类脚本快速接入"},
	})
	// 运维工具平台基础信息（描述/语言/产品文档/所属组=应用运维部）
	opsToolApp.Description = "运维工具平台：面向 SRE 的一站式自动化巡检与告警联动工具台，聚合 CMDB 与监控数据，支撑日常运维操作"
	opsToolApp.Language = "Go"
	opsToolApp.DocURL = "https://docs.example.com/ops-tool/manual"
	opstoolOG := opsApp.ID
	opsToolApp.OwnerGroupID = &opstoolOG
	deps.Apps.Update(opsToolApp)

	// 应用市场富展示：各应用网络信息 + 鉴权方式（应用市场详情页渲染）
	seedAppMeta(deps, monitorApp, model.JSONMap{
		"cloud": "自建机房", "account": "-", "region": "cn-east-1",
		"vpc": "vpc-monitor", "subnet": "subnet-monitor-1", "sg": "sg-monitor-prod",
	}, model.JSONAny{
		map[string]any{"icon": "🔑", "name": "OAuth 2.0 · Client Credentials", "type": "oauth2_client_credentials", "strength": "high", "strengthLabel": "高",
			"desc": "应用间调用首选：以应用身份换取短期 JWT，网关统一校验，支持最小权限范围"},
		map[string]any{"icon": "🎫", "name": "静态 Token", "type": "static_token", "strength": "medium", "strengthLabel": "中",
			"desc": "适合轻量、长期稳定的服务调用，Token 由 owner 签发"},
	})
	seedAppMeta(deps, itsmApp, model.JSONMap{
		"cloud": "阿里云", "account": "acn-itsm", "region": "cn-hangzhou",
		"vpc": "vpc-itsm", "subnet": "subnet-itsm-app", "sg": "sg-itsm-app",
	}, model.JSONAny{
		map[string]any{"icon": "🔑", "name": "OAuth 2.0 · Authorization Code", "type": "oauth2_auth_code", "strength": "high", "strengthLabel": "高",
			"desc": "人工访问首选：走企业 SSO 登录后换取访问令牌，支持用户级审计"},
		map[string]any{"icon": "🔧", "name": "API Key", "type": "api_key", "strength": "medium", "strengthLabel": "中",
			"desc": "SDK 接入常用：请求头携带固定 Key，适合工具类脚本"},
	})
	seedAppMeta(deps, cloudApp, model.JSONMap{
		"cloud": "腾讯云", "account": "act-ops", "region": "ap-guangzhou",
		"vpc": "vpc-cloud", "subnet": "subnet-cloud-1", "sg": "sg-cloud-prod",
	}, model.JSONAny{
		map[string]any{"icon": "🔑", "name": "OAuth 2.0 · Client Credentials", "type": "oauth2_client_credentials", "strength": "high", "strengthLabel": "高",
			"desc": "云资源操作强烈建议使用：应用级凭证，配合数据范围字段实现最小权限"},
		map[string]any{"icon": "🎫", "name": "静态 Token", "type": "static_token", "strength": "medium", "strengthLabel": "中",
			"desc": "适合只读查询类调用，支持按接口前缀限定范围"},
		map[string]any{"icon": "👤", "name": "OIDC 单点登录（SSO）", "type": "oidc", "strength": "high", "strengthLabel": "高",
			"desc": "人工登录控制台使用，对接企业统一身份，登录态自动过期"},
	})

	// 4.2 演示应用：小黄的监控服务 / 小红的数据分析
	xiaohuangApp := seedApp(deps, cfg, "xiaohuang-monitor", "小黄的监控服务", userID(deps, "xiaohuang"))
	xiaohongApp := seedApp(deps, cfg, "xiaohong-analytics", "小红的数据分析", userID(deps, "xiaohong"))
	ensureOwner(deps, xiaohuangApp.ID, userID(deps, "xiaohuang"), true)
	ensureOwner(deps, xiaohongApp.ID, userID(deps, "xiaohong"), true)

	// 5. 权限点
	readAction := seedAction(deps, app.ID, "cmdb:host:read", "read", "host", "读取主机详情")
	listAction := seedAction(deps, app.ID, "cmdb:host:list", "list", "host", "列举主机列表")
	createAction := seedAction(deps, app.ID, "cmdb:host:create", "create", "host", "创建主机记录")
	_ = seedAction(deps, app.ID, "cmdb:host:update", "update", "host", "更新主机属性")
	_ = seedAction(deps, app.ID, "cmdb:host:delete", "delete", "host", "删除主机记录")
	readActionIDs := []uint64{readAction.ID, listAction.ID}
	_ = []uint64{readAction.ID, listAction.ID, createAction.ID}

	// 5.0 富 Demo 数据：补齐应用市场/能力市场内容
	// （cmdb 主机管理/数据库管理/财务数据、itsm 工单接口、cloudportal 公共资源池）
	seedRichDemoData(deps)

	// 5.1 小黄的监控服务 — 能力包"主机监控"
	{
		// 权限点（唯一 code，避免与 monitor 应用冲突）
		monListAct := seedAction(deps, xiaohuangApp.ID, "xh-monitor:host:list", "list", "host", "列举主机列表")
		monReadAct := seedAction(deps, xiaohuangApp.ID, "xh-monitor:host:read", "read", "host", "读取主机详情")
		monCreateAct := seedAction(deps, xiaohuangApp.ID, "xh-monitor:host:create", "create", "host", "创建监控任务")

		// 能力包（幂等：先查后建）
		monCap := findOrCreateCapability(deps, xiaohuangApp.ID, "主机监控", "主机资源的只读/管理监控能力",
			"published", userID(deps, "xiaohuang"),
			model.JSONAny{
				map[string]any{"name": "env", "type": "string", "desc": "环境"},
				map[string]any{"name": "region", "type": "string", "desc": "地域"},
			},
			model.JSONAny{
				map[string]any{
					"id": "readonly", "name": "只读监控", "status": "published",
					"action_codes":  []any{"xh-monitor:host:list", "xh-monitor:host:read"},
					"grantee_types": []any{"user", "org"},
					"data_control":  true, "data_models": []any{"host"},
				},
				map[string]any{
					"id": "full", "name": "完整监控", "status": "draft",
					"action_codes":  []any{"xh-monitor:host:list", "xh-monitor:host:read", "xh-monitor:host:create"},
					"grantee_types": []any{"user", "org"},
					"data_control":  true, "data_models": []any{"host"},
				},
			},
			model.StringArray{"主机", "监控", "只读"},
			[]uint64{monListAct.ID, monReadAct.ID, monCreateAct.ID},
		)
		log.Printf("[seed] capability 主机监控 id=%d presets=2", monCap.ID)
		// 主机监控 readonly 预设的范围选项（演示：数据范围表单有选项可选）
		seedScopeOptions(deps, monCap.ID, "readonly", "host", []*model.ScopeOption{
			{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
			{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要监控的主机实例", API: "/api/v1/hosts"},
			{Type: model.ScopeOptSelect, Label: "选择环境", Desc: "选择目标环境（单选）", Field: "env", Op: "==",
				Choices: model.JSONAny{
					map[string]any{"label": "生产环境", "value": "prod"},
					map[string]any{"label": "预发布", "value": "staging"},
				}},
		})
	}

	// 5.2 小红的数据分析 — 能力包"数据分析"（纯接口，无数据模型）
	{
		daReadAct := seedAction(deps, xiaohongApp.ID, "xh-analytics:report:read", "read", "report", "读取分析报告")
		daListAct := seedAction(deps, xiaohongApp.ID, "xh-analytics:report:list", "list", "report", "列举分析报告")
		daReadIDs := []uint64{daReadAct.ID, daListAct.ID}

		daCap := findOrCreateCapability(deps, xiaohongApp.ID, "数据分析", "数据分析报告的查看与列举能力",
			"published", userID(deps, "xiaohong"),
			nil,
			model.JSONAny{
				map[string]any{
					"id": "viewer", "name": "报告查看", "status": "published",
					"action_codes":  []any{"xh-analytics:report:list", "xh-analytics:report:read"},
					"grantee_types": []any{"user"},
				},
			},
			model.StringArray{"分析", "报告"},
			daReadIDs,
		)
		log.Printf("[seed] capability 数据分析 id=%d presets=1", daCap.ID)
	}

	// 5.3 运维工具平台（ops-tool）自有权限点与数据模型
	// 消费方工具也有对外 API 与自有资源目录：方向为运维（巡检/告警/运维作业），与 cmdb 基础设施资源区分
	{
		seedToolAction(deps, opsToolApp.ID, "ops-tool:inspection:list", "list", "inspection", "列举巡检任务",
			"GET", "/api/v1/inspections",
			"GET /api/v1/inspections?page=1&page_size=20",
			`{"items":[{"id":1,"name":"每日全量巡检","scope":"web-01,web-02","status":"running"}],"total":1}`)
		seedToolAction(deps, opsToolApp.ID, "ops-tool:inspection:run", "run", "inspection", "触发巡检任务",
			"POST", "/api/v1/inspections",
			"POST /api/v1/inspections\n{\"name\":\"上线前巡检\",\"scope\":[\"web-01\",\"db-01\"]}",
			`{"id":2,"name":"上线前巡检","status":"queued"}`)
		seedToolAction(deps, opsToolApp.ID, "ops-tool:alert:list", "list", "alert", "查询告警记录",
			"GET", "/api/v1/alerts",
			"GET /api/v1/alerts?level=critical",
			`{"items":[{"id":1,"level":"critical","source":"cmdb","status":"open"}],"total":1}`)
		seedToolAction(deps, opsToolApp.ID, "ops-tool:alert:ack", "ack", "alert", "确认告警",
			"POST", "/api/v1/alerts/{id}/ack",
			"POST /api/v1/alerts/1/ack",
			`{"id":1,"status":"acknowledged"}`)
		seedToolAction(deps, opsToolApp.ID, "ops-tool:runbook:execute", "execute", "runbook", "执行运维作业",
			"POST", "/api/v1/runbooks/{id}/execute",
			"POST /api/v1/runbooks/3/execute\n{\"params\":{\"batch\":10}}",
			`{"execution_id":"rb-20260815-001","status":"running"}`)
		log.Printf("[seed] ops-tool actions=5")
		// 自有资源目录（区别于 cmdb 的基础设施资源，AppID 归属本应用）
		seedResourceModel(deps, opsToolApp.ID, 101, "inspection", "巡检任务", model.JSONMap{
			"cron": "string", "scope": "string", "status": "string",
		})
		seedResourceModel(deps, opsToolApp.ID, 102, "alert", "告警记录", model.JSONMap{
			"level": "string", "source": "string", "status": "string",
		})
		seedResourceModel(deps, opsToolApp.ID, 103, "runbook", "运维作业", model.JSONMap{
			"name": "string", "target": "string", "timeout_sec": "number",
		})
		log.Printf("[seed] ops-tool resource_models=3")
	}

	// 6. 授权（通过申请单）
	grantViaRequest(deps, ctx, userID(deps, "alice"), app.ID, "user:alice:cmdb-read",
		model.ReqSubjectUser, userID(deps, "alice"), readActionIDs, nil,
		"alice 为 cmdb 联合负责人，需要只读权限", "", false)
	// （1.5 T3）强一致档（force-remote）已随投影退役——点查即实时，无前置同步对象

	// 7. 程序身份（M2M）
	secret := "cloud-mgmt-secret"
	hash, _ := auth.HashPassword(secret)
	if _, err := deps.Apps.ClientByID("cloud-mgmt"); err != nil {
		deps.Apps.CreateClient(&model.Client{
			AppID:            app.ID,
			ClientID:         "cloud-mgmt",
			ClientSecretHash: hash,
			Status:           model.StatusEnabled,
		})
	}

	// 7.1 运维工具应用（消费方视角）
	opsToolHash, _ := auth.HashPassword("ops-tool-secret")
	if _, err := deps.Apps.ClientByID("ops-tool-client"); err != nil {
		deps.Apps.CreateClient(&model.Client{
			AppID:            opsToolApp.ID,
			ClientID:         "ops-tool-client",
			ClientSecretHash: opsToolHash,
			Status:           model.StatusEnabled,
		})
	}

	// 运维工具接入 cmdb 的授权（已通过）
	if cli, err := deps.Apps.ClientByID("ops-tool-client"); err == nil {
		grantViaRequest(deps, ctx, userID(deps, "frank"), app.ID, "service:ops-tool:cmdb-read",
			model.ReqSubjectApp, cli.ID, readActionIDs, nil,
			"运维工具平台需要只读接入 CMDB，用于自动化巡检", "", false)
	}

	// 运维工具接入 monitor 的授权（申请中）
	if cli, err := deps.Apps.ClientByID("ops-tool-client"); err == nil {
		monitorRead := seedAction(deps, monitorApp.ID, "monitor:host:read", "read", "host", "读取监控数据")
		grantViaRequest(deps, ctx, userID(deps, "frank"), monitorApp.ID, "service:ops-tool:monitor-read",
			model.ReqSubjectApp, cli.ID, []uint64{monitorRead.ID}, nil,
			"运维工具平台需要只读接入监控，用于告警联动", "", true)
	}

	// 8. 同步
	deps.CMDBConnector.SetAppID(app.ID)
	deps.CMDBConnector.SyncModels(ctx)
	deps.CMDBConnector.SyncInstances(ctx)
	deps.IdentityConn.Sync(ctx)
	// 8.0 数据契约行（A2/A4）：投影就绪后起确认制时钟——巡检与判定门槛立即可读
	seedContractRows(deps, app.ID)
	// 身份同步可能新建组织（path 为 mock-identity id），以本地组织树为准重算物化路径
	refreshAllOrgPaths(deps)

	// 8.1 OpenAPI 同步（幂等）：cmdb 应用生成权限点 method/path + 板块模板
	// PEP（Traefik forwardAuth / mock-cmdb 网关）依赖 actions.method/path 做"请求→action"映射，
	// 数据卷重建后 seed 需一并恢复，否则网关返回 "no action resolved"。
	if app.OpenAPIURL == "" {
		app.OpenAPIURL = "http://mock-cmdb:8090/openapi.json"
		if err := deps.Apps.Update(app); err != nil {
			log.Printf("[seed] openapi url update warn: %v", err)
		}
	}
	if res, err := deps.OpenAPISyncer.Sync(ctx, app); err != nil {
		log.Printf("[seed] openapi sync warn: %v", err)
	} else {
		log.Printf("[seed] openapi sync done: %v", res)
	}

	// 8.2 爱丽丝演示权限（须在资源模型/实例同步之后：自建组限定实例范围）
	seedAliceDemo(deps, ctx)

	// 9. 应用版本（放在最后：前面的 Apps.Update（如 OpenAPI 同步）会用旧对象覆盖 version 字段）
	seedAppVersions(deps)

	log.Println("[seed] done. 登录: admin/admin123; M2M: cloud-mgmt/cloud-mgmt-secret; 演示: xiaohuang/pass123 xiaohong/pass123")
	return nil
}

func seedUser(deps *api.Deps, username, displayName string, orgID uint64, isAdmin bool) {
	hash, _ := auth.HashPassword("pass123")
	u := &model.User{
		Username:     username,
		DisplayName:  displayName,
		Email:        username + "@iam.local",
		PasswordHash: hash,
		Status:       model.StatusEnabled,
		Source:       model.SourceLocal,
	}
	if err := deps.Users.Create(u); err != nil {
		u, _ = deps.Users.ByUsername(username)
	}
	// 所有种子用户都挂到所属组织：组长=admin 角色，普通成员=member 角色
	// （修复：原实现仅 isAdmin=true 才加成员，导致 bob/dave/xiaohuang/xiaohong 无组织身份）
	if orgID > 0 {
		role := int16(model.GroupRoleMember)
		if isAdmin {
			role = model.GroupRoleAdmin
		}
		deps.Groups.AddMember(&model.UserGroup{UserID: u.ID, GroupID: orgID, Role: role})
	}
}

func seedApp(deps *api.Deps, cfg *config.Config, code, name string, ownerID uint64) *model.App {
	app := &model.App{
		Code:    code,
		Name:    name,
		Type:    1,
		Status:  model.StatusEnabled,
		OwnerID: ownerID,
	}
	if err := deps.Apps.Create(app); err != nil {
		log.Printf("[seed] app %s exists", code)
		apps, _, _ := deps.Apps.List(0, 100)
		for _, a := range apps {
			if a.Code == code {
				app = &a
				break
			}
		}
	}
	// 注册者落 app_owners 主负责人：/users/me 与「应用管理」均基于 app_owners 返回，
	// 不落表则 owner 在自己账号里看不到管理的应用（幂等：重复执行由唯一索引 idx_ao 兜底）
	deps.Apps.AddOwner(&model.AppOwner{AppID: app.ID, UserID: ownerID, IsPrimary: true})
	return app
}

func seedAppMeta(deps *api.Deps, app *model.App, netInfo model.JSONMap, auth model.JSONAny) {
	app.NetInfo = netInfo
	app.Auth = auth
	deps.Apps.Update(app)
}

// seedAppVersions 为各应用设置展示版本号（详情页/市场展示，避免 v—）
func seedAppVersions(deps *api.Deps) {
	versions := map[string]string{
		"cmdb": "2.4.1", "monitor": "2.3.0", "itsm": "1.8.0",
		"ops-tool": "0.3.0", "cloudportal": "3.0.1",
		"xiaohuang-monitor": "1.0.0", "xiaohong-analytics": "1.0.0",
	}
	for code, ver := range versions {
		a := appByCode(deps, code)
		if a == nil || a.Version == ver {
			continue
		}
		a.Version = ver
		deps.Apps.Update(a)
	}
}

func seedAction(deps *api.Deps, appID uint64, code, operation, resource, desc string) *model.Action {
	a := &model.Action{
		AppID:     appID,
		Code:      code,
		Operation: operation,
		Resource:  resource,
		Name:      desc,
	}
	deps.Access.UpsertAction(a)
	// 已存在时 UpsertAction 不回填 ID → 需重新查取 ID（否则权限点引用 [0,0] 失效）
	if a.ID == 0 {
		if act, err := deps.Access.ActionByCode(appID, code); err == nil {
			return act
		}
	}
	return a
}

// seedToolAction 创建带 method/path/示例的权限点（模拟 OpenAPI 同步产物，供应用详情接口树展示）
func seedToolAction(deps *api.Deps, appID uint64, code, operation, resource, name, method, path, req, resp string) *model.Action {
	a := seedAction(deps, appID, code, operation, resource, name)
	if a.Method == method && a.Path == path && a.ReqExample == req && a.RespExample == resp {
		return a
	}
	a.Method, a.Path = method, path
	a.ReqExample, a.RespExample = req, resp
	deps.Access.UpsertAction(a)
	if act, err := deps.Access.ActionByCode(appID, code); err == nil {
		return act
	}
	return a
}

// seedResourceModel 为指定应用插入自有资源模型（幂等：按 code 查；demo 中 cmdb 模型来自 mock-cmdb 同步，
// 其他应用的自有资源目录直接在 seed 投影，SourceID 用高位偏移避免与同步源 id 冲突）
func seedResourceModel(deps *api.Deps, appID uint64, sourceID uint64, code, name string, schema model.JSONMap) {
	if _, err := deps.Res.ModelByCode(code); err == nil {
		return
	}
	if _, err := deps.Res.UpsertModel(&model.ResourceModel{
		SourceID:         sourceID,
		AppID:            appID,
		Code:             code,
		Name:             name,
		AttributesSchema: schema,
	}); err != nil {
		log.Printf("[seed] resource model %s warn: %v", code, err)
	}
}

// seedContractSpecs 数据域契约默认值（种子专用）：host 用短承诺（SLA 15s / 上限 30s）——
// ⚠️ 设计约束：**巡检周期必须显著小于 SLA**（否则两次巡检之间 age 必超 SLA，Fresh 态不可达、stale 常驻）
// demo 组合 = PATROL_INTERVAL 5s / SLA 15s / max 30s → 正常 fresh、停上游 40s 内演示 Expired 三态
// （清单 2.3.1 时序走查）；字段只取基础判定字段（白名单恒可算）
var seedContractSpecs = map[string]map[string]any{
	"host":            {"fields": []any{"name", "owner_id"}, "algorithm": "L2", "staleness_sla_sec": 15, "degrade_max_age_sec": 30},
	"database":        {"fields": []any{"name", "owner_id"}, "algorithm": "L2", "staleness_sla_sec": 300, "degrade_max_age_sec": 0},
	"public_resource": {"fields": []any{"name"}, "algorithm": "L1", "staleness_sla_sec": 300, "degrade_max_age_sec": 0},
}

// withDataContractMeta 预设回填契约元数据（幂等）：data_control 预设缺 data_contract →
// 按数据域套默认契约——让发布链路门禁（ensureDataContracts）对种子能力可正向通过（清单 A2）
func withDataContractMeta(presets model.JSONAny) model.JSONAny {
	for _, raw := range presets {
		p, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		if dc, _ := p["data_control"].(bool); !dc {
			continue
		}
		if _, has := p["data_contract"]; has {
			continue
		}
		dms, _ := p["data_models"].([]any)
		if len(dms) == 0 {
			continue
		}
		mc, _ := dms[0].(string)
		if spec, ok := seedContractSpecs[mc]; ok {
			p["data_contract"] = spec
		}
	}
	return presets
}

// seedContractRows 数据契约行种子（清单 A2/A4）：确认制时钟起钟、增量水位空（首轮巡检从零拉）；
// 巡检按契约域遍历、无投影域（如 public_resource）自动跳过，判定门槛同款跳过——不误伤
func seedContractRows(deps *api.Deps, appID uint64) {
	for mc, spec := range seedContractSpecs {
		fields := []string{}
		for _, f := range spec["fields"].([]any) {
			fields = append(fields, f.(string))
		}
		sla, _ := spec["staleness_sla_sec"].(int)
		maxAge, _ := spec["degrade_max_age_sec"].(int)
		if _, err := deps.Contracts.UpsertContract(&model.DataContract{
			AppID: appID, ModelCode: mc, Fields: fields,
			Algorithm: spec["algorithm"].(string), StalenessSlaSec: sla, DegradeMaxAgeSec: maxAge,
		}); err != nil {
			log.Printf("[seed] contract %s warn: %v", mc, err)
		}
	}
	log.Printf("[seed] data contracts ready (host: sla=15s/max=30s — 分钟级新鲜度三态演示；巡检 5s < SLA)")
}

func findOrCreateOrg(deps *api.Deps, name string, parentID *uint64) *model.Group {
	// 幂等：先按 (name, parent_id) 精确查找，避免重复创建
	existing, err := deps.Groups.FindOrgByNameParent(name, parentID, 0)
	if err == nil && existing != nil {
		return existing
	}
	g := &model.Group{
		Name:     name,
		Type:     model.GroupTypeOrg,
		ParentID: parentID,
		Status:   model.StatusEnabled,
	}
	if err := deps.Groups.Create(g); err != nil {
		// 并发创建兜底：再查一次
		existing, _ = deps.Groups.FindOrgByNameParent(name, parentID, 0)
		if existing != nil {
			return existing
		}
		log.Printf("[seed] WARN findOrCreateOrg create failed: %v", err)
	}
	return g
}

func ensureOwner(deps *api.Deps, appID, userID uint64, isPrimary bool) {
	deps.Apps.AddOwner(&model.AppOwner{AppID: appID, UserID: userID, IsPrimary: isPrimary})
}

// findOrCreateCapability 幂等创建能力包（先按 name 查，不存在则建 + 关联权限点）
func findOrCreateCapability(deps *api.Deps, appID uint64, name, desc, status string, ownerID uint64,
	modelFields, presets model.JSONAny, tags model.StringArray, actionIDs []uint64,
) *model.CapabilityManifest {
	presets = withDataContractMeta(presets) // A2：契约元数据注入（创建路径）
	// 查找已有
	caps, _ := deps.Caps.List(appID)
	for _, c := range caps {
		if c.Name == name {
			// 幂等自愈：早期种子的能力包缺 data_contract → 原地回填后保存（发布门禁可正向通过）
			withDataContractMeta(c.Presets)
			if err := deps.Caps.Update(&c); err != nil {
				log.Printf("[seed] heal capability %q contract meta warn: %v", name, err)
			}
			return &c
		}
	}
	// 创建
	m := &model.CapabilityManifest{
		AppID:           appID,
		Name:            name,
		Description:     desc,
		Version:         1,
		Status:          status,
		Visibility:      model.VisPublic,
		GranteeTypes:    model.StringArray{model.GranteeUser, model.GranteeOrg},
		EnforcementMode: "gateway",
		CreatedBy:       ownerID,
		UpdatedBy:       ownerID,
		ModelFields:     modelFields,
		Presets:         presets,
		Tags:            tags,
	}
	if err := deps.Caps.Create(m); err != nil {
		log.Printf("[seed] create capability %q failed: %v", name, err)
		return &model.CapabilityManifest{}
	}
	// 关联权限点
	for _, aid := range actionIDs {
		deps.DB.Create(&model.CapabilityAction{
			CapabilityID:  m.ID,
			ActionID:      aid,
			AllowedScopes: model.StringArray{"all"},
			DefaultScope:  "all",
		})
	}
	return m
}

func grantViaRequest(deps *api.Deps, ctx context.Context, applicantID, appID uint64, name string,
	subjectType int16, subjectID uint64, actionIDs []uint64, dataScope model.JSONMap,
	reason string, scopeType string, pending bool) {
	var status int16 = model.ReqApproved
	if pending {
		status = model.ReqPending
	}
	// 映射 grantee_type 字符串（Policy 用字符串，AccessRequest 也用字符串）
	granteeType := "user"
	switch subjectType {
	case model.ReqSubjectGroup, model.ReqSubjectOrg:
		granteeType = "group"
	case model.ReqSubjectApp:
		granteeType = "app"
	}
	// 申请主体（与前端自助申请对齐，listUpstreams「我接入了谁」按此归集）：
	// 用户申请=applicantID；下游应用申请=申请方 App.ID（grantee 是 client，反查其 AppID）
	applicantSubjectType := int16(model.ReqSubjectUser)
	applicantSubjectID := applicantID
	if subjectType == model.ReqSubjectApp {
		applicantSubjectType = int16(model.ReqSubjectApp)
		if cl, err := deps.Apps.ClientByRowID(subjectID); err == nil {
			applicantSubjectID = cl.AppID
		}
	}
	req := &model.AccessRequest{
		AppID:                appID,
		ApplicantID:          applicantID,
		ApplicantSubjectType: applicantSubjectType,
		ApplicantSubjectID:   applicantSubjectID,
		RequestType:          model.RequestApply,
		Status:               status,
		GranteeType:          granteeType,
		GranteeID:            subjectID,
		Reason:               reason,
		RiskLevel:            1,
		Content: model.JSONMap{
			"action_ids": actionIDs,
			"data_scope": dataScope,
			"scope_type": scopeType,
		},
	}
	if err := deps.DB.Create(req).Error; err != nil {
		log.Printf("[seed] request %s failed: %v", name, err)
		return
	}

	// 如果是已批准，创建策略
	if status == model.ReqApproved {
		// 映射 Policy.SubjectType（申请主体类型 → 策略主体类型）
		// ReqSubjectApp(4) → SubjectService(3)，避免落库为 4 导致 authz/upstreams 按 3 查询不到
		policySubjectType := subjectType
		switch subjectType {
		case model.ReqSubjectUser:
			policySubjectType = model.SubjectUser
		case model.ReqSubjectGroup, model.ReqSubjectOrg:
			policySubjectType = model.SubjectGroup
		case model.ReqSubjectApp:
			policySubjectType = model.SubjectService
		}
		p := &model.Policy{
			AppID:       appID,
			Name:        name,
			ActionIDs:   actionIDs,
			SubjectType: policySubjectType,
			SubjectID:   subjectID,
			Effect:      model.EffectAllow,
			Status:      model.PolicyActive,
			Source:      model.SourceViaRequest,
			RequestID:   &req.ID,
		}
		deps.DB.Create(p)
	}
}

func userID(deps *api.Deps, username string) uint64 {
	u, _ := deps.Users.ByUsername(username)
	return u.ID
}

func actionsFor(deps *api.Deps, appID uint64, ops ...string) []uint64 {
	acts, _ := deps.Access.Actions(appID)
	var ids []uint64
	for _, a := range acts {
		for _, op := range ops {
			if a.Operation == op {
				ids = append(ids, a.ID)
			}
		}
	}
	return ids
}

func dedupPolicies(deps *api.Deps) {
	// 简化：不做去重
}

// cleanupDuplicateOrgs 清理重复的组织组（历史 seed 多次运行残留）
// 按 name 分组（忽略 parent_id 差异），保留 path 最完整的，合并成员/权限后删除冗余
func cleanupDuplicateOrgs(deps *api.Deps) {
	allGroups, err := deps.Groups.Tree()
	if err != nil {
		return
	}
	type key struct {
		Name string
		Type int16
	}
	grouped := map[key][]model.Group{}
	for _, g := range allGroups {
		if g.Type != model.GroupTypeOrg {
			continue
		}
		k := key{Name: g.Name, Type: g.Type}
		grouped[k] = append(grouped[k], g)
	}
	var cleaned int
	for _, gs := range grouped {
		if len(gs) <= 1 {
			continue
		}
		// 保留 path 最长的（最完整的树形路径），若一样长取 ID 最小
		keeper := gs[0]
		for _, g := range gs[1:] {
			if len(g.Path) > len(keeper.Path) || (len(g.Path) == len(keeper.Path) && g.ID < keeper.ID) {
				keeper = g
			}
		}
		for _, g := range gs {
			if g.ID == keeper.ID {
				continue
			}
			// 迁移 user_groups: 把旧组成员移到 keeper（先删 keeper 已有的避免冲突）
			var members []model.UserGroup
			deps.DB.Where("group_id = ?", g.ID).Find(&members)
			for _, m := range members {
				var exists int64
				deps.DB.Model(&model.UserGroup{}).Where("user_id = ? AND group_id = ?", m.UserID, keeper.ID).Count(&exists)
				if exists == 0 {
					m.GroupID = keeper.ID
					deps.DB.Save(&m)
				} else {
					deps.DB.Delete(&m)
				}
			}
			// 迁移 group_permissions（组接口权限）
			deps.DB.Table("group_permissions").Where("group_id = ?", g.ID).
				Update("group_id", keeper.ID)
			// 迁移 policies（subject_type=2=group, subject_id=g.ID → keeper.ID）
			deps.DB.Table("policies").Where("subject_type = ? AND subject_id = ?",
				model.SubjectGroup, g.ID).Update("subject_id", keeper.ID)
			// 迁移 access_requests 的 group 关联
			// 删除冗余组及其孤儿子树
			deleteOrphanSubtree(deps, g.ID)
			cleaned++
		}
		log.Printf("[seed] cleanupDuplicateOrgs: cleaned %d duplicate org groups for %d names", cleaned, len(grouped))
	}
	// 补修复：确保所有组织组的 path 正确
	refreshAllOrgPaths(deps)
}

// deleteOrphanSubtree 递归删除孤儿子树（没有成员的叶子节点）
func deleteOrphanSubtree(deps *api.Deps, groupID uint64) {
	// 先删子节点
	var children []model.Group
	deps.DB.Where("parent_id = ?", groupID).Find(&children)
	for _, c := range children {
		deleteOrphanSubtree(deps, c.ID)
	}
	// 删组
	deps.DB.Delete(&model.Group{}, groupID)
}

// refreshAllOrgPaths 重建所有组织组的物化路径
// 注意：父组织 id 恒小于子组织 id（seed 先建父后建子），故按 id 升序保证父先于子；
// 且必须用切片元素指针就地更新（deps.DB.Save(g) 用同一指针），子节点才能读到最新父 path
func refreshAllOrgPaths(deps *api.Deps) {
	allGroups, err := deps.Groups.Tree()
	if err != nil {
		return
	}
	sort.Slice(allGroups, func(i, j int) bool { return allGroups[i].ID < allGroups[j].ID })
	idMap := map[uint64]*model.Group{}
	for i := range allGroups {
		idMap[allGroups[i].ID] = &allGroups[i]
	}
	for i := range allGroups {
		g := &allGroups[i]
		if g.Type != model.GroupTypeOrg || g.ParentID == nil {
			// 根节点
			expected := "/" + strconv.FormatUint(g.ID, 10) + "/"
			if g.Path != expected {
				g.Path = expected
				deps.DB.Save(g)
			}
			continue
		}
		var expected string
		if p, ok := idMap[*g.ParentID]; ok && p.Path != "" {
			expected = p.Path + strconv.FormatUint(g.ID, 10) + "/"
		} else {
			expected = "/" + strconv.FormatUint(g.ID, 10) + "/"
		}
		if g.Path != expected {
			g.Path = expected
			deps.DB.Save(g)
		}
	}
}

// ==================== 富 Demo 数据（v12：应用市场 / 能力市场内容） ====================

// resetDemoData 清空全部 demo 域表并重置自增序列（seed --reset 一键重建）
// （1.5 T3）OpenFGA 已退役——重置仅涉及下列关系表
func resetDemoData(db *gorm.DB) error {
	tables := "scope_options, capability_actions, capability_manifests, capability_publish_tasks, " +
		"revoke_requests, access_requests, approval_tasks, policies, policy_versions, clients, app_owners, apps, actions, " +
		"resource_models, resource_instances, group_permissions, user_groups, groups, users, sync_jobs, bundles, " +
		"policy_templates, template_actions, permission_templates, agent_statuses, audit_logs, decision_logs"
	return db.Exec("TRUNCATE TABLE " + tables + " RESTART IDENTITY CASCADE").Error
}

// appByCode 按 code 查找应用
func appByCode(deps *api.Deps, code string) *model.App {
	apps, _, _ := deps.Apps.List(0, 200)
	for _, a := range apps {
		if a.Code == code {
			return &a
		}
	}
	return nil
}

// actionID 按 app+code 解析权限点 ID（不存在则补建）
func actionID(deps *api.Deps, appID uint64, code, operation, resource, name string) uint64 {
	if act, err := deps.Access.ActionByCode(appID, code); err == nil {
		return act.ID
	}
	return seedAction(deps, appID, code, operation, resource, name).ID
}

// seedActionEndpoint 带 method/path/接口契约的权限点（市场卡片接口树展示用）
func seedActionEndpoint(deps *api.Deps, appID uint64, code, operation, resource, name, method, path, req, resp string) *model.Action {
	a := seedAction(deps, appID, code, operation, resource, name)
	a.Method = method
	a.Path = path
	a.ReqExample = req
	a.RespExample = resp
	deps.Access.UpsertAction(a)
	return a
}

// capActionRows 能力→权限点关联（默认全量范围）
func capActionRows(actionIDs []uint64) []*model.CapabilityAction {
	rows := make([]*model.CapabilityAction, 0, len(actionIDs))
	for _, aid := range actionIDs {
		rows = append(rows, &model.CapabilityAction{
			ActionID:      aid,
			AllowedScopes: model.StringArray{"all"},
			DefaultScope:  "all",
		})
	}
	return rows
}

// upsertCapability 幂等创建/更新能力包：按 (app, name) 匹配；presets/字段/标签/动作以最新 seed 为准自愈
func upsertCapability(deps *api.Deps, appID uint64, name, desc, status string, ownerID uint64,
	modelFields, presets model.JSONAny, tags model.StringArray, actionIDs []uint64,
) *model.CapabilityManifest {
	presets = withDataContractMeta(presets) // A2：data_control 预设回填契约元数据（发布门禁对种子能力可正向通过）
	caps, _ := deps.Caps.List(appID)
	for i := range caps {
		if caps[i].Name == name {
			c := &caps[i]
			c.Description = desc
			c.Status = status
			if c.Visibility == "" {
				c.Visibility = model.VisPublic
			}
			c.EnforcementMode = "gateway"
			c.ModelFields = modelFields
			c.Presets = presets
			c.Tags = tags
			c.UpdatedBy = ownerID
			if err := deps.Caps.Update(c); err != nil {
				log.Printf("[seed] update capability %q warn: %v", name, err)
			}
			deps.Caps.SetActions(c.ID, capActionRows(actionIDs))
			return c
		}
	}
	m := &model.CapabilityManifest{
		AppID:           appID,
		Name:            name,
		Description:     desc,
		Version:         1,
		Status:          status,
		Visibility:      model.VisPublic,
		GranteeTypes:    model.StringArray{model.GranteeUser, model.GranteeOrg},
		EnforcementMode: "gateway",
		CreatedBy:       ownerID,
		UpdatedBy:       ownerID,
		ModelFields:     modelFields,
		Presets:         presets,
		Tags:            tags,
	}
	if err := deps.Caps.Create(m); err != nil {
		log.Printf("[seed] create capability %q failed: %v", name, err)
		return &model.CapabilityManifest{}
	}
	deps.Caps.SetActions(m.ID, capActionRows(actionIDs))
	return m
}

// seedScopeOptions 幂等写入某预设×数据模型的范围选项（覆盖写，v12 独立表）
func seedScopeOptions(deps *api.Deps, capID uint64, presetID, modelCode string, opts []*model.ScopeOption) {
	if capID == 0 {
		return
	}
	if err := deps.Caps.ReplaceScopeOptions(capID, presetID, modelCode, opts); err != nil {
		log.Printf("[seed] scope options warn cap=%d preset=%s model=%s: %v", capID, presetID, modelCode, err)
	}
}

// seedRichDemoData v12 富 Demo 数据：补齐应用市场/能力市场内容
// cmdb 主机管理（readonly/operator/full 预设 + 6 类范围选项）、数据库管理、财务数据；
// itsm 工单接口；cloudportal 公共资源池。全部幂等自愈，重复执行安全。
func seedRichDemoData(deps *api.Deps) {
	cmdb := appByCode(deps, "cmdb")
	itsm := appByCode(deps, "itsm")
	cloud := appByCode(deps, "cloudportal")
	if cmdb == nil || itsm == nil || cloud == nil {
		log.Printf("[seed] WARN seedRichDemoData: required app missing (cmdb/itsm/cloudportal)")
		return
	}
	adminID := userID(deps, "admin")

	// ---- 接口契约 actions（OpenAPI 同步不含 db/cloud/itsm 域）----
	seedActionEndpoint(deps, cmdb.ID, "cmdb:db:list", "list", "database", "列举数据库实例", "GET", "/api/v1/databases", "", `{"items":[{"id":1,"db_name":"db-cmdb","owner_dept":"效能部门"}]}`)
	seedActionEndpoint(deps, cmdb.ID, "cmdb:db:read", "read", "database", "读取数据库详情", "GET", "/api/v1/databases/{id}", "", `{"id":1,"db_name":"db-cmdb","backup_policy":"daily"}`)
	seedActionEndpoint(deps, cmdb.ID, "cmdb:db:backup", "update", "database", "触发数据库备份", "POST", "/api/v1/databases/{id}/backup", `{"type":"full"}`, `{"job":"bk-001","status":"running"}`)
	seedActionEndpoint(deps, cmdb.ID, "cmdb:db:delete", "delete", "database", "删除数据库实例", "DELETE", "/api/v1/databases/{id}", "", `{"deleted":2}`)
	seedActionEndpoint(deps, itsm.ID, "itsm:ticket:list", "list", "ticket", "获取工单列表", "GET", "/api/v1/tickets", "", `{"items":[{"id":1001,"assignee":"bob","status":"open"}]}`)
	seedActionEndpoint(deps, itsm.ID, "itsm:ticket:read", "read", "ticket", "获取工单详情", "GET", "/api/v1/tickets/{id}", "", `{"id":1001,"title":"磁盘扩容","assignee":"bob"}`)
	seedActionEndpoint(deps, itsm.ID, "itsm:ticket:create", "create", "ticket", "创建工单", "POST", "/api/v1/tickets", `{"title":"磁盘扩容","priority":"high"}`, `{"id":1002,"status":"open"}`)
	seedActionEndpoint(deps, itsm.ID, "itsm:ticket:update", "update", "ticket", "更新工单状态", "PUT", "/api/v1/tickets/{id}", `{"status":"processing"}`, `{"id":1002,"status":"processing"}`)
	seedActionEndpoint(deps, cloud.ID, "cloud:resource:list", "list", "public_resource", "获取公共资源列表", "GET", "/api/v1/resources", "", `{"items":[{"id":1,"account":"acc-ops-001"}]}`)
	seedActionEndpoint(deps, cloud.ID, "cloud:resource:create", "create", "public_resource", "创建资源", "POST", "/api/v1/resources", `{"account":"acc-ops-001","type":"ecs"}`, `{"id":2}`)
	seedActionEndpoint(deps, cloud.ID, "cloud:resource:delete", "delete", "public_resource", "释放资源", "DELETE", "/api/v1/resources/{id}", "", `{"released":2}`)

	// ===== cmdb · 主机管理（cap id 1，演示主入口）=====
	hostCap := upsertCapability(deps, cmdb.ID, "主机管理",
		"主机资源生命周期管理：只读/运维/完整三档预设 + 6 类数据范围选项",
		"published", adminID,
		model.JSONAny{
			map[string]any{"name": "id", "type": "integer", "desc": "主机唯一ID"},
			map[string]any{"name": "name", "type": "string", "desc": "主机名（全局唯一）"},
			map[string]any{"name": "ip", "type": "string", "desc": "内网 IP"},
			map[string]any{"name": "org_id", "type": "string", "desc": "所属组织"},
			map[string]any{"name": "owner_id", "type": "string", "desc": "负责人"},
			map[string]any{"name": "env", "type": "string", "desc": "环境（prod/staging/dev）"},
			map[string]any{"name": "tags", "type": "string", "desc": "标签"},
		},
		model.JSONAny{
			map[string]any{
				// T6 升级版（§4.2）：host→disk 层级编排 + 场景参数联动（只选一次防域间错位）
				"id": "readonly", "name": "只读查看", "status": "published",
				"action_codes":  []any{"cmdb:host:list", "cmdb:host:read", "cmdb:disk:list", "cmdb:disk:read"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  true, "data_models": []any{"host", "disk"},
				"param_linkage": "shared",
				"scenario_params": []any{
					map[string]any{"key": "account", "label": "云账号", "type": "select", "required": true,
						"choices": []any{
							map[string]any{"label": "运维账号", "value": "acc-ops-001"},
							map[string]any{"label": "研发账号", "value": "acc-rd-002"},
						}},
				},
				"data_model_tree": []any{
					map[string]any{"model": "host", "children": []any{
						map[string]any{"model": "disk"},
					}},
				},
			},
			map[string]any{
				"id": "operator", "name": "运维操作", "status": "published",
				"action_codes":  []any{"cmdb:host:list", "cmdb:host:create", "cmdb:host:update"},
				"grantee_types": []any{"app"},
				"data_control":  false, "data_models": []any{},
			},
			map[string]any{
				"id": "full", "name": "完整管理", "status": "draft",
				"action_codes":  []any{"cmdb:host:list", "cmdb:host:create", "cmdb:host:update", "cmdb:host:delete"},
				"grantee_types": []any{"app"},
				"data_control":  false, "data_models": []any{},
			},
		},
		model.StringArray{"主机", "CMDB", "生命周期", "host"},
		[]uint64{
			actionID(deps, cmdb.ID, "cmdb:host:list", "list", "host", "列举主机列表"),
			actionID(deps, cmdb.ID, "cmdb:host:read", "read", "host", "读取主机详情"),
			actionID(deps, cmdb.ID, "cmdb:host:create", "create", "host", "创建主机记录"),
			actionID(deps, cmdb.ID, "cmdb:host:update", "update", "host", "更新主机属性"),
			actionID(deps, cmdb.ID, "cmdb:host:delete", "delete", "host", "删除主机记录"),
		},
	)
	seedScopeOptions(deps, hostCap.ID, "readonly", "host", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		// T6 联动绑定域（§4.2 升级一）：field=account 与场景参数 key 同名——
		// shared 模式下值只认 "$account" 引用（申请时只选一次，服务端钉子防域间错位）
		{Type: model.ScopeOptSelect, Label: "按云账号（联动）", Desc: "场景参数联动——全域同值，防错位", Field: "account", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "运维账号", "value": "acc-ops-001"},
				map[string]any{"label": "研发账号", "value": "acc-rd-002"},
			}},
		{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要访问的主机实例", API: "/api/v1/hosts"},
		{Type: model.ScopeOptSelect, Label: "选择环境", Desc: "选择目标环境（单选）", Field: "env", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "生产环境", "value": "prod"},
				map[string]any{"label": "预发布", "value": "staging"},
				map[string]any{"label": "开发环境", "value": "dev"},
			}},
		{Type: model.ScopeOptMultiSelect, Label: "选择云账号", Desc: "选择要访问的云账号（可多选）", Field: "account_id", Op: "in",
			Choices: model.JSONAny{
				map[string]any{"label": "运维账号", "value": "acc-ops-001"},
				map[string]any{"label": "研发账号", "value": "acc-rd-002"},
				map[string]any{"label": "测试账号", "value": "acc-test-003"},
			}},
		{Type: model.ScopeOptVariable, Label: "仅自己的资源", Desc: "自动匹配你的身份，只能看到自己创建的资源", Field: "owner_id", Op: "==", Variable: model.VarCurrentUser, VarLabel: "当前用户"},
		{Type: model.ScopeOptInput, Label: "按标签过滤", Desc: "输入标签名进行模糊匹配", Field: "tags", Op: "contains", Placeholder: "如 web、prod"},
	})
	// T6 层级从属域（§4.2 升级二）：disk 随 host——落底层各域仍是独立策略（层级是编排不是存储）
	seedScopeOptions(deps, hostCap.ID, "readonly", "disk", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		// 与 host 域同 key 联动：shared 模式下同一次 account 选定带出全域（结构上不可能错位）
		{Type: model.ScopeOptSelect, Label: "按云账号（联动）", Desc: "随 host 域场景参数——全域同值", Field: "account", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "运维账号", "value": "acc-ops-001"},
				map[string]any{"label": "研发账号", "value": "acc-rd-002"},
			}},
		{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要访问的磁盘实例", API: "/api/v1/disks"},
	})

	// ===== cmdb · 数据库管理（published）=====
	dbCap := upsertCapability(deps, cmdb.ID, "数据库管理",
		"数据库实例管理：查看对全员开放，变更操作仅限 DBA 组",
		"published", adminID,
		model.JSONAny{
			map[string]any{"name": "id", "type": "integer", "desc": "数据库ID"},
			map[string]any{"name": "db_name", "type": "string", "desc": "库名"},
			map[string]any{"name": "owner_dept", "type": "string", "desc": "所属部门"},
			map[string]any{"name": "backup_policy", "type": "string", "desc": "备份策略"},
		},
		model.JSONAny{
			map[string]any{
				"id": "dbview", "name": "数据库查看", "status": "published",
				"action_codes":  []any{"cmdb:db:list", "cmdb:db:read"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  true, "data_models": []any{"database"},
			},
			map[string]any{
				"id": "dba", "name": "DBA 管理", "status": "published",
				"action_codes":  []any{"cmdb:db:list", "cmdb:db:backup", "cmdb:db:delete"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  true, "data_models": []any{"database"},
			},
		},
		model.StringArray{"数据库", "CMDB", "DBA"},
		[]uint64{
			actionID(deps, cmdb.ID, "cmdb:db:list", "list", "database", "列举数据库实例"),
			actionID(deps, cmdb.ID, "cmdb:db:read", "read", "database", "读取数据库详情"),
			actionID(deps, cmdb.ID, "cmdb:db:backup", "update", "database", "触发数据库备份"),
			actionID(deps, cmdb.ID, "cmdb:db:delete", "delete", "database", "删除数据库实例"),
		},
	)
	seedScopeOptions(deps, dbCap.ID, "dbview", "database", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要访问的数据库实例", API: "/api/v1/databases"},
		{Type: model.ScopeOptSelect, Label: "选择数据库", Desc: "从预设数据库中选择（单选）", Field: "db_name", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "CMDB 库", "value": "db-cmdb"},
				map[string]any{"label": "订单库", "value": "db-order"},
			}},
		{Type: model.ScopeOptVariable, Label: "仅本部门数据", Desc: "自动匹配你的所属部门", Field: "owner_dept", Op: "==", Variable: model.VarCurrentOrg, VarLabel: "当前组织"},
	})
	seedScopeOptions(deps, dbCap.ID, "dba", "database", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		{Type: model.ScopeOptSelect, Label: "选择数据库", Desc: "从预设数据库中选择（单选）", Field: "db_name", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "CMDB 库", "value": "db-cmdb"},
				map[string]any{"label": "订单库", "value": "db-order"},
				map[string]any{"label": "全部生产库", "value": "db-prod-*"},
			}},
		{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要访问的数据库实例", API: "/api/v1/databases"},
	})

	// ===== cmdb · 财务数据（draft / hidden，市场不可见）=====
	_ = upsertCapability(deps, cmdb.ID, "财务数据",
		"财务敏感数据（草稿/隐身，仅白名单直链可见）",
		"draft", adminID,
		model.JSONAny{
			map[string]any{"name": "id", "type": "integer", "desc": "账目ID"},
		},
		model.JSONAny{
			map[string]any{
				"id": "fin", "name": "财务查看", "status": "draft",
				"action_codes":  []any{"cmdb:db:list"},
				"grantee_types": []any{"user"},
				"data_control":  true, "data_models": []any{"database"},
			},
		},
		model.StringArray{"财务", "敏感"},
		[]uint64{actionID(deps, cmdb.ID, "cmdb:db:list", "list", "database", "列举数据库实例")},
	)

	// ===== itsm · 工单接口（published，纯接口）=====
	_ = upsertCapability(deps, itsm.ID, "工单接口",
		"ITSM 工单接口：查看/处理，数据隔离由 ITSM 自身 assignee 逻辑保证",
		"published", adminID,
		model.JSONAny{
			map[string]any{"name": "id", "type": "integer", "desc": "工单ID"},
			map[string]any{"name": "title", "type": "string", "desc": "标题"},
			map[string]any{"name": "assignee_id", "type": "string", "desc": "分配人"},
			map[string]any{"name": "status", "type": "string", "desc": "状态（open/processing/done）"},
		},
		model.JSONAny{
			map[string]any{
				"id": "view", "name": "工单查看", "status": "published",
				"action_codes":  []any{"itsm:ticket:list", "itsm:ticket:read"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  false, "data_models": []any{},
			},
			map[string]any{
				"id": "handle", "name": "工单处理", "status": "published",
				"action_codes":  []any{"itsm:ticket:create", "itsm:ticket:update"},
				"grantee_types": []any{"app"},
				"data_control":  false, "data_models": []any{},
			},
		},
		model.StringArray{"工单", "ITSM"},
		[]uint64{
			actionID(deps, itsm.ID, "itsm:ticket:list", "list", "ticket", "获取工单列表"),
			actionID(deps, itsm.ID, "itsm:ticket:read", "read", "ticket", "获取工单详情"),
			actionID(deps, itsm.ID, "itsm:ticket:create", "create", "ticket", "创建工单"),
			actionID(deps, itsm.ID, "itsm:ticket:update", "update", "ticket", "更新工单状态"),
		},
	)

	// ===== cloudportal · 公共资源池（published）=====
	cloudCap := upsertCapability(deps, cloud.ID, "公共资源池",
		"公共云资源（仅运维中心可见）",
		"published", adminID,
		model.JSONAny{
			map[string]any{"name": "account_id", "type": "string", "desc": "云账号"},
			map[string]any{"name": "tag_dept", "type": "string", "desc": "部门标签"},
			map[string]any{"name": "region", "type": "string", "desc": "地域"},
		},
		model.JSONAny{
			map[string]any{
				"id": "viewer", "name": "资源查看", "status": "published",
				"action_codes":  []any{"cloud:resource:list"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  true, "data_models": []any{"public_resource"},
			},
			map[string]any{
				"id": "manager", "name": "资源管理", "status": "published",
				"action_codes":  []any{"cloud:resource:list", "cloud:resource:create", "cloud:resource:delete"},
				"grantee_types": []any{"user", "org", "group", "app"},
				"data_control":  true, "data_models": []any{"public_resource"},
			},
		},
		model.StringArray{"云", "公共资源", "cloudportal"},
		[]uint64{
			actionID(deps, cloud.ID, "cloud:resource:list", "list", "public_resource", "获取公共资源列表"),
			actionID(deps, cloud.ID, "cloud:resource:create", "create", "public_resource", "创建资源"),
			actionID(deps, cloud.ID, "cloud:resource:delete", "delete", "public_resource", "释放资源"),
		},
	)
	seedScopeOptions(deps, cloudCap.ID, "viewer", "public_resource", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		{Type: model.ScopeOptMultiSelect, Label: "选择云账号", Desc: "选择要查看的云账号（可多选）", Field: "account_id", Op: "in",
			Choices: model.JSONAny{
				map[string]any{"label": "运维账号", "value": "acc-ops-001"},
				map[string]any{"label": "研发账号", "value": "acc-rd-002"},
			}},
		{Type: model.ScopeOptSelect, Label: "选择地域", Desc: "选择目标地域", Field: "region", Op: "==",
			Choices: model.JSONAny{
				map[string]any{"label": "广州", "value": "ap-guangzhou"},
				map[string]any{"label": "上海", "value": "ap-shanghai"},
			}},
		{Type: model.ScopeOptVariable, Label: "仅自己账号的资源", Desc: "自动匹配你负责的云账号", Field: "account_id", Op: "==", Variable: model.VarCurrentAccount, VarLabel: "当前账号"},
	})
	seedScopeOptions(deps, cloudCap.ID, "manager", "public_resource", []*model.ScopeOption{
		{Type: model.ScopeOptAll, Label: "所有数据", Desc: "无需填写"},
		{Type: model.ScopeOptInstance, Label: "具体实例", Desc: "勾选要访问的资源", API: "/api/v1/resources"},
	})

	log.Printf("[seed] rich demo data done: cmdb 主机管理/数据库管理/财务数据, itsm 工单接口, cloudportal 公共资源池")
}

// ==================== 爱丽丝演示权限（个人/组织/自建组，能力包维度） ====================

// capByName 按 (app, name) 查找能力包
func capByName(deps *api.Deps, appID uint64, name string) *model.CapabilityManifest {
	caps, _ := deps.Caps.List(appID)
	for _, c := range caps {
		if c.Name == name {
			return &c
		}
	}
	return &model.CapabilityManifest{}
}

// orgByName 按名称查找组织
func orgByName(deps *api.Deps, name string) *model.Group {
	gs, _ := deps.Groups.Tree()
	for _, g := range gs {
		if g.Type == model.GroupTypeOrg && g.Name == name {
			return &g
		}
	}
	return &model.Group{}
}

// findOrCreateCustomGroup 幂等创建自建组（创建者即组长）
func findOrCreateCustomGroup(deps *api.Deps, name string, ownerID uint64) *model.Group {
	gs, _ := deps.Groups.Tree()
	for i := range gs {
		if gs[i].Type == model.GroupTypeCustom && gs[i].Name == name {
			return &gs[i]
		}
	}
	g := &model.Group{Name: name, Type: model.GroupTypeCustom, Source: model.SourceLocal, Status: model.StatusEnabled}
	if err := deps.Groups.Create(g); err != nil {
		log.Printf("[seed] create custom group %q failed: %v", name, err)
		return &model.Group{}
	}
	g.Path = "/" + strconv.FormatUint(g.ID, 10) + "/"
	deps.Groups.Update(g)
	deps.Groups.AddMember(&model.UserGroup{UserID: ownerID, GroupID: g.ID, Role: model.GroupRoleAdmin})
	return g
}

// ensureGroupMember 幂等加成员
func ensureGroupMember(deps *api.Deps, groupID, userID uint64, role int16) {
	var n int64
	deps.DB.Model(&model.UserGroup{}).Where("user_id = ? AND group_id = ?", userID, groupID).Count(&n)
	if n > 0 {
		return
	}
	deps.Groups.AddMember(&model.UserGroup{UserID: userID, GroupID: groupID, Role: role})
}

// ensureGroupPermission 幂等给组挂权限点（组即角色）
func ensureGroupPermission(deps *api.Deps, groupID uint64, actionID uint64) {
	var n int64
	deps.DB.Model(&model.GroupPermission{}).Where("group_id = ? AND action_id = ?", groupID, actionID).Count(&n)
	if n > 0 {
		return
	}
	deps.DB.Create(&model.GroupPermission{GroupID: groupID, ActionID: actionID})
}

// presetActionIDs 解析能力包预设的 action_codes → 权限点 ID
func presetActionIDs(deps *api.Deps, cap *model.CapabilityManifest, presetID string) []uint64 {
	var ids []uint64
	for _, raw := range cap.Presets {
		p, _ := raw.(map[string]any)
		if p == nil || p["id"] != presetID {
			continue
		}
		if v, ok := p["action_codes"].([]any); ok {
			for _, x := range v {
				code, _ := x.(string)
				if act, err := deps.Access.ActionByCode(cap.AppID, code); err == nil {
					ids = append(ids, act.ID)
				}
			}
		}
	}
	return ids
}

// seedDataScope 种子数据级范围：nil = 全部；Type=instance = 限定实例（写 OpenFGA tuple 真实生效）
type seedDataScope struct {
	Model     string   // 数据模型 code（如 host）
	Type      string   // model.ScopeOptAll | model.ScopeOptInstance
	Instances []string // instance 类型：资源实例 external ids（如 host-4）
}

// grantCapabilityViaRequest 已通过的能力包申请单 + 策略落库（“我的权限”展示 & 授权真实生效）
// 幂等：同一 grantee × 能力包 × 预设 已有已通过申请单则跳过，避免重复 seed 产生重复授权
// scope=nil 表示数据范围“全部”；scope.Type=instance 时落 Policy.ResourceScope 的 instance_ids（集合式范围谓词，判定=点查行 id 比对）
func grantCapabilityViaRequest(deps *api.Deps, ctx context.Context, applicantID, appID, capID uint64, presetID, granteeType, granteeName string, granteeID uint64, scope *seedDataScope, reason string) {
	var existing int64
	deps.DB.Model(&model.AccessRequest{}).
		Where("status = ? AND grantee_type = ? AND grantee_id = ? AND content->>'capability_id' = ? AND content->>'preset_id' = ?",
			model.ReqApproved, granteeType, granteeID, strconv.FormatUint(capID, 10), presetID).
		Count(&existing)
	if existing > 0 {
		return
	}
	cap, err := deps.Caps.ByID(capID)
	if err != nil {
		log.Printf("[seed] grantCapability warn: capability %d: %v", capID, err)
		return
	}
	ids := presetActionIDs(deps, cap, presetID)

	// 数据范围：展示（Content.scope_selections）与真实生效（Policy.ResourceScope——集合式=点查行 id 比对）
	var scopeSel model.JSONAny
	var resScope model.JSONMap
	dataScopeType := ""
	expr := "// 无数据层限制（all 类型）"
	switch {
	case scope != nil && scope.Type == model.ScopeOptInstance:
		scopeSel = model.JSONAny{map[string]any{
			"model": scope.Model, "type": "instance",
			"selectedValue": "", "selectedValues": toAnyStrings(scope.Instances),
		}}
		resScope = model.JSONMap{
			"type": "instance", "model": scope.Model, "operation": "read",
			"instance_ids": toAnyFloats(instanceIDsByExternal(deps, scope.Model, scope.Instances)),
		}
		dataScopeType = "instance"
		expr = "// 集合式范围谓词（勾选实例——判定：点查行 id ∈ 集合）\n"
		for _, ext := range scope.Instances {
			expr += fmt.Sprintf("(%s:%s, reader, %s)\n", scope.Model, ext, granteeName)
		}
	case scope != nil && scope.Type == model.ScopeOptAll:
		scopeSel = model.JSONAny{map[string]any{
			"model": scope.Model, "type": "all",
			"selectedValue": "", "selectedValues": []any{},
		}}
		expr = fmt.Sprintf("// 无数据层限制（%s 全部）\n", scope.Model)
	}

	req := &model.AccessRequest{
		ApplicantID:          applicantID,
		RequestType:          model.RequestApply,
		ApplicantSubjectType: model.ReqSubjectUser,
		ApplicantSubjectID:   applicantID,
		GranteeType:          granteeType,
		GranteeName:          granteeName,
		GranteeID:            granteeID,
		ScopeSelections:      scopeSel,
		AppID:                appID,
		Content: model.JSONMap{
			"capability_id":     float64(capID),
			"preset_id":         presetID,
			"scope_selections":  scopeSel,
			"scope_expression":  expr,
			"expression_engine": "CheckRow",
		},
		Reason:    reason,
		RiskLevel: model.RiskLow,
		Status:    model.ReqApproved,
	}
	if err := deps.DB.Create(req).Error; err != nil {
		log.Printf("[seed] capability request warn: %v", err)
		return
	}
	policySubjectType := int16(model.SubjectUser)
	switch granteeType {
	case model.GranteeOrg, model.GranteeGroup:
		policySubjectType = model.SubjectGroup
	case model.GranteeApp:
		policySubjectType = model.SubjectService
	}
	p := &model.Policy{
		AppID:         appID,
		Name:          fmt.Sprintf("cap:%s:%s", presetID, granteeName),
		ActionIDs:     ids,
		SubjectType:   policySubjectType,
		SubjectID:     granteeID,
		Effect:        model.EffectAllow,
		Status:        model.PolicyActive,
		Source:        model.SourceViaRequest,
		RequestID:     &req.ID,
		ResourceScope: resScope,
		DataScopeType: dataScopeType,
	}
	if err := deps.DB.Create(p).Error; err != nil {
		log.Printf("[seed] capability policy warn: %v", err)
		return
	}
	// （1.5 T3）集合式判定=点查行比对（CheckRow）——不再物化 OpenFGA 元组；
	// 组级授权的成员关系也不再需要物化（主体闭包由 Casbin/策略快照处理）
}

func toAnyStrings(ss []string) []any {
	out := make([]any, 0, len(ss))
	for _, s := range ss {
		out = append(out, s)
	}
	return out
}

func toAnyFloats(ids []uint64) []any {
	out := make([]any, 0, len(ids))
	for _, id := range ids {
		out = append(out, float64(id))
	}
	return out
}

// instanceIDsByExternal 按数据模型 code + external ids 解析资源实例 DB ID
func instanceIDsByExternal(deps *api.Deps, modelCode string, externals []string) []uint64 {
	m, err := deps.Res.ModelByCode(modelCode)
	if err != nil {
		return nil
	}
	var ids []uint64
	for _, ext := range externals {
		if inst, err := deps.Res.InstanceByExternal(m.ID, ext); err == nil {
			ids = append(ids, inst.ID)
		}
	}
	return ids
}

// seedAliceDemo 爱丽丝演示权限：自建组 + 个人/组织/自建组 三个维度的能力包授权
// 数据范围差异化：个人/组织 = 全部；自建组 = 限定主机实例（web-01/web-02，集合式范围谓词）
func seedAliceDemo(deps *api.Deps, ctx context.Context) {
	alice := userID(deps, "alice")
	cmdb := appByCode(deps, "cmdb")
	itsm := appByCode(deps, "itsm")
	cloud := appByCode(deps, "cloudportal")
	hostCap := capByName(deps, cmdb.ID, "主机管理")
	dbCap := capByName(deps, cmdb.ID, "数据库管理")
	itsmCap := capByName(deps, itsm.ID, "工单接口")
	cloudCap := capByName(deps, cloud.ID, "公共资源池")

	// ---- 1. 自建组：主机运维小组（alice 组长，含成员与组权限点）----
	grp := findOrCreateCustomGroup(deps, "主机运维小组", alice)
	ensureGroupMember(deps, grp.ID, alice, model.GroupRoleAdmin)
	ensureGroupMember(deps, grp.ID, userID(deps, "bob"), model.GroupRoleMember)
	ensureGroupMember(deps, grp.ID, userID(deps, "xiaohuang"), model.GroupRoleMember)
	// 组权限点（动作级，非能力包）：CMDB 主机只读
	ensureGroupPermission(deps, grp.ID, actionID(deps, cmdb.ID, "cmdb:host:read", "read", "host", "读取主机详情"))
	ensureGroupPermission(deps, grp.ID, actionID(deps, cmdb.ID, "cmdb:host:list", "list", "host", "列举主机列表"))

	// ---- 2. 个人权限（能力包维度，数据范围：全部）----
	if hostCap.ID > 0 {
		grantCapabilityViaRequest(deps, ctx, alice, cmdb.ID, hostCap.ID, "readonly", model.GranteeUser, "alice", alice,
			&seedDataScope{Model: "host", Type: model.ScopeOptAll},
			"作为 cmdb 联合负责人，申请主机管理只读能力（演示）")
	}
	if cloudCap.ID > 0 {
		grantCapabilityViaRequest(deps, ctx, alice, cloud.ID, cloudCap.ID, "viewer", model.GranteeUser, "alice", alice,
			&seedDataScope{Model: "public_resource", Type: model.ScopeOptAll},
			"跨团队协作：申请云管公共资源只读能力（演示）")
	}

	// ---- 2.1 Bob 个人权限（能力包维度，数据范围：全部）----
	bob := userID(deps, "bob")
	if itsmCap.ID > 0 && bob > 0 {
		grantCapabilityViaRequest(deps, ctx, bob, itsm.ID, itsmCap.ID, "view", model.GranteeUser, "bob", bob, nil,
			"Bob 负责工单处理，申请 ITSM 工单查看能力（演示）")
	}

	// ---- 3. 组织权限（能力包维度 → 研发一部，数据范围：全部）----
	rd1 := orgByName(deps, "研发一部")
	if itsmCap.ID > 0 && rd1.ID > 0 {
		grantCapabilityViaRequest(deps, ctx, alice, itsm.ID, itsmCap.ID, "view", model.GranteeOrg, rd1.Name, rd1.ID, nil,
			"研发一部全员：ITSM 工单查看能力（组织级授权，演示）")
	}
	if dbCap.ID > 0 && rd1.ID > 0 {
		grantCapabilityViaRequest(deps, ctx, alice, cmdb.ID, dbCap.ID, "dbview", model.GranteeOrg, rd1.Name, rd1.ID,
			&seedDataScope{Model: "database", Type: model.ScopeOptAll},
			"研发一部全员：CMDB 数据库查看能力（组织级授权，演示）")
	}
	// ---- 3.1 研发一部组织权限（动作级）：CMDB 主机只读（组织成员自动继承，工作台计数口径一致）----
	if rd1.ID > 0 {
		ensureGroupPermission(deps, rd1.ID, actionID(deps, cmdb.ID, "cmdb:host:read", "read", "host", "读取主机详情"))
		ensureGroupPermission(deps, rd1.ID, actionID(deps, cmdb.ID, "cmdb:host:list", "list", "host", "列举主机列表"))
	}

	// ---- 4. 自建组权限（能力包维度 → 主机运维小组，数据范围：限定主机实例 web-01/web-02）----
	if hostCap.ID > 0 && grp.ID > 0 {
		grantCapabilityViaRequest(deps, ctx, alice, cmdb.ID, hostCap.ID, "readonly", model.GranteeGroup, grp.Name, grp.ID,
			&seedDataScope{Model: "host", Type: model.ScopeOptInstance, Instances: []string{"host-4", "host-5"}},
			"主机运维小组共享：CMDB 主机只读能力（仅 web-01/web-02 主机实例，演示限定数据范围）")
	}

	log.Printf("[seed] alice demo permissions done: personal=2(全部) org=2(全部) group=1(限定实例 host-4,host-5)")
}
