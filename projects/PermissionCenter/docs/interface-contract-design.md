# 能力包接口契约设计（2026-08-12）

## 背景

系统设计：注册应用 → 能力打包 → 发布 → 申请授权。

对「人 / 组织」的申请：作用主体是人，会访问系统界面操作，有无接口契约不影响使用。

对「程序（M2M / 下游应用）」的申请：程序需要**直接调用 API 接口**，必须知道：
1. 调用哪些接口（method + path）
2. 每个接口的参数（request / response schema）
3. 数据范围条件（scope_expression）
4. 鉴权方式

而当前能力包维度**完全没有暴露接口契约** —— 这是设计遗漏。

## 决策：方案 A（能力包内联接口契约）为主 + 用户文档为辅

### 1. 接口契约（机器可读，核心）

- 每个能力包 / 预设 = N 个接口，申请方可见：
  - `method + path`（已有：`Action.method/path`，OpenAPI 同步填充）
  - 请求示例 `req_example`（OpenAPI `requestBody` → JSON 示例）
  - 响应示例 `resp_example`（OpenAPI `responses` → JSON 示例）
  - 数据范围条件（scope_expression，申请时生成）
  - 鉴权方式（应用 `auth` 声明）
- 数据链路（已具备大部分，补断点）：
  - `Action` 已有 `method/path/req_example/resp_example` 字段
  - **断点 1**：`ReqExample/RespExample` 从未被填充 —— OpenAPI 解析器需解析 `requestBody/responses` 生成 JSON 示例
  - **断点 2**：`enrichPresets` 已解析出 `ops`（method/path/name），但前端只展示 action code —— 需升级为接口明细表

### 2. 用户文档（人可读，辅助）

- `App.DocURL` 新字段：产品文档 / 操作手册 / 自写 API 指南链接
- **纯展示性字段**，不参与任何同步 / 解析
- 挂载点：
  - 应用详情「基础信息」板块
  - 应用市场公开详情（`marketplaceAppDetail`）
  - 能力包详情 / 申请预览（透传所属应用 doc_url）

### 3. 双文档互补理念

| 文档 | 用途 | 给谁看 | 能否替代 |
|------|------|--------|---------|
| `openapi_url`（接口契约） | 机器解析：同步权限点/能力、生成接口明细 | 系统内部 + 程序对接方 | 普通人看不懂 |
| `doc_url`（产品文档/手册） | 人可读：操作手册、业务说明、自写 API 指南 | 申请方 / 管理员 / 新人 | 机器无法解析 |

> 类比：Stripe 的 API Reference（契约）+ Guides（说明）双文档。

## OpenAPI vs Swagger（背景澄清）

- **OpenAPI 是 Swagger 规范的后继者**（2015 年捐给 Linux 基金会后改名），不是两个不同接口
- OpenAPI 3 与 Swagger 2.0 结构差异：
  - 顶层：`openapi: 3.0.0` vs `swagger: 2.0`
  - 组件：`components/schemas` vs `definitions`
  - 请求体：`requestBody` vs `body` 参数（`in: body`）
- **决策**：注册只填一个 `openapi_url`（同源文档，无需两个 URL）；demo 项目暂不做 Swagger 2.0 解析兼容，仅在注册表单用提示卡片说明"兼容 OpenAPI 3 / Swagger 2 格式，解析器自动识别"

## 字段变更

```go
// App 模型新增
DocURL string `gorm:"size:512" json:"doc_url"` // 产品文档/操作手册链接（人可读，纯展示）
```

## 落地清单

后端：
1. `App` 加 `DocURL` 字段（AutoMigrate 自动加列）
2. `registerAppReq` / `registerApp` 支持 `doc_url`
3. `appDetail` 返回 `doc_url`
4. `marketplaceAppDetail` 返回 `doc_url`
5. seed 给 cmdb 补演示 doc_url

前端：
6. 注册表单：OpenAPI 配置区加提示卡片（兼容说明）+ 产品文档输入框
7. `AppDetail` 基础信息板块展示 doc_url
8. 应用市场公开详情展示 doc_url

## 后续工作（未做，本迭代范围外）

- OpenAPI 解析器补 `requestBody/responses` → 生成 `req_example/resp_example`（能力包接口明细的核心）
- 能力市场申请预览：预设卡片升级为接口明细表（method+path+可展开示例）
- "我接入了谁"增加接口契约视图（程序对接方）
- Swagger 2.0 解析兼容（demo 不做）
