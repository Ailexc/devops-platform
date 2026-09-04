# 全家桶 SSO 账号作用域改造方案（方案 1 · 系统前缀账号）

> 状态：待评审（评审后按此实施）
> 范围：Authentication 认证中心 / 门户 / LDAP 与 7 个子系统的账号命名与 SSO 收口
> 目标：演示不混乱、账号全局唯一、SSO 三种接入能力照常真实演示、各系统本地数据/中文名零改动

---

## 1. 背景与问题

当前"全家桶统一认证"把认证中心 12 个全局用户名（admin / zhangsan / lisi / wangwu …）经 SSO 下发到各系统，引发三类混乱：

1. **用户名冲突 / 语义错位**：各系统本地都有 `admin`（且角色不同），认证中心唯一的 `admin` 进哪个系统都命中"本地 admin"，导致同一账号在不同系统忽强忽弱（如工单里 admin 不是超管、看不到流程测试等管理功能）。
2. **静默建空用户**：SSO 收口处用 `get_or_create`，把张三/李四等静默建进没有其数据的系统（工单库里出现了无组、无工单的 `zhangsan`/`lisi` 垃圾用户），登录成功却一片空白，观感像"坏掉"。
3. **门户分组与本地数据不一致**：认证中心 `demo_systems` 标记过宽（张三被标在工单/云管分组，但那些系统本地并没有张三的数据）。

> 注意：Release/工单"数据没 seed、审批空、Demo App 无发布"等属于**数据 seed 缺失**问题（与本方案正交），已在部署脚本单独补齐（5.5~5.8），不在此重复。

## 2. 决策结论（经讨论确认）

- **不还原**历史接入，**在当前基础**上改造（改动收敛在"账号命名 + SSO 收口映射"两层）。
- 采用 **方案 1：系统前缀账号 + 完全隔离**，而非"精简成 admin+两三人全系统同名"（后者需重做各系统角色画像与存量数据，且要求数据强一致，维护成本高、破坏各系统既有叙事）。
- **每系统独立账号体系**（沿用各系统本地历史账号/角色/数据）；**门户 = SSO 便捷入口**（真实演示 OIDC / JWKS / 网关 forwardAuth 三种接入）。
- 认证中心/LDAP 账号**全局唯一**：`<系统前缀>_<本名>`（如 `release_zhangsan`、`workflow_admin`、`iam_alice`），从根上避免 `admin` 等通用名撞车。
- **前缀只在登录/认证层**：SSO 收口处剥掉本系统前缀、映射回系统本地本名 → **系统内部显示与数据仍是本地中文名（张三/爱丽丝），一个字符都不用改**；LDAP/认证中心的 `displayName` 也照常存中文（登录下拉显示"张三 (release_zhangsan)"）。
- 某系统未开通的账号：认证中心不注册其前缀账号 + 门户分组不出现；若仍发生"本地无此用户"，SSO 收口**明确报错（403 未在此系统开通）**，绝不静默建空用户。

## 3. 目标架构

```
 ┌──────────────────────── 认证中心 / LDAP（唯一账号，英文前缀）────────────────────────┐
 │  门户登录下拉（按系统分组）                                                        │
 │   发布系统: release_admin / release_zhangsan / release_lisi / release_wangwu       │
 │   工单系统: workflow_admin / workflow_xiaoming / workflow_xiaoli / …              │
 │   云管系统: cloud_admin / cloud_ops_user / …                                       │
 │   权限中心: iam_admin / iam_alice / iam_bob / iam_erin                             │
 │   任务/事件: cmdb_* / event_*（方式二，可后续决定是否收口）                        │
 └───────────────┬──────────────────────────────────────────────────────────────────┘
                 │ SSO 三种接入（OIDC 授权码 / 直连 JWKS / 网关 forwardAuth）
                 ▼
       各系统 SSO 收口：剥本系统前缀 → 查本地账号
                 │
                 ▼
      系统本地（zhangsan + display_name 张三 + 角色/数据）—— 中文名、UI、数据全不动
```

## 4. 命名规范

- 前缀 = 系统短名（ASCII，小写）+ `_`；本名沿用现有本地用户名（ASCII）。
- 例：`release_zhangsan`、`workflow_xiaoming`、`cloud_ops_user`、`iam_alice`、`cmdb_wangwu`、`event_liuyi`。
- `displayName` / `cn` 保留中文（张三 / 爱丽丝 / 云管理员）。
- 认证中心签发 JWT 的 `uid`、网关 `X-Auth-Username`、OIDC `preferred_username` 均为带前缀账号；**各系统收口处按本系统前缀剥离后查本地**。
- 每系统本地数据完全不动（包括 release 支付线负责人 `zhangsan` 等）。

## 5. 每系统账号清单（草案，待评审确认）

> 原则：只放"该系统本地有演示数据/角色的用户"。列表可按演示需要增删。

### 5.1 ReleaseManager 发布系统（本地 12 用户，演示核心 4 人）
| 认证中心账号 | 系统本地 | 中文 | 本地角色 / 演示数据 |
|---|---|---|---|
| `release_admin` | admin | 管理员 | 超管（全部应用/审批） |
| `release_zhangsan` | zhangsan | 张三 | 支付业务线负责人（payment 应用群发布） |
| `release_lisi` | lisi | 李四 | 电商/订单业务线（待确认 leader 归属） |
| `release_wangwu` | wangwu | 王五 | 审批人 / 测试（发布审批链） |

其余本地用户（zhaoliu/qianqi/sunba…）不入认证中心 → 不进门户分组（系统内仍可自洽，若需演示可选再加）。

### 5.2 WorkFlowCenter 工单系统（本地 seed 8 人 + admin）
| 认证中心账号 | 系统本地 | 中文 | 本地角色 / 演示数据 |
|---|---|---|---|
| `workflow_admin` | admin | 管理员 | 超管（含流程测试 / 管理后台） |
| `workflow_xiaoming` | xiaoming | 小明 | 研发组（发起/处理工单） |
| `workflow_xiaoli` | xiaoli | 小李 | IT 运维组·部门主管（审批） |
| `workflow_xiaohong` | xiaohong | 小红 | 研发组（抄送/协同） |

> 本地库中被 SSO 静默建出的 `zhangsan`/`lisi` 垃圾用户将随收口改造移除。

### 5.3 CloudManager 云管系统（本地 4 人）
| 认证中心账号 | 系统本地 | 中文 | 本地角色 / 演示数据 |
|---|---|---|---|
| `cloud_admin` | admin | 系统管理员 | 超管 |
| `cloud_cloud_admin` | cloud_admin | 云管理员 | 云平台组（云资源管理） |
| `cloud_ops_user` | ops_user | 运维工程师 | 运维（云资源操作） |
| `cloud_readonly` | readonly | 只读用户 | 只读 |

### 5.4 PermissionCenter 权限中心（本地 7 人）
| 认证中心账号 | 系统本地 | 中文 | 本地角色 / 演示数据 |
|---|---|---|---|
| `iam_admin` | admin | 管理员 | 超管（IAM 全量） |
| `iam_alice` | alice | 爱丽丝 | 研发中心（资源申请/授权） |
| `iam_bob` | bob | 鲍勃 | 研发中心（被授权方） |
| `iam_erin` | erin | 艾琳 | 运维平台（审计/审批） |

### 5.5 TaskManager / EventManager（方式二 · 直连 JWKS，各 1 个演示账号）
| 认证中心账号 | 系统本地 | 中文 | 演示内容 |
|---|---|---|---|
| `cmdb_wangwu` | wangwu | 王五 | 任务管理 / 资源调度大屏（测试部） |
| `event_ops_user` | ops_user | 运维工程师 | 事件 / 告警处理（运维部） |

- 两个系统相对无权限诉求，各收口为 1 个白名单账号；其它认证账号一律 403（防垃圾账号）。

### 5.6 门户/认证中心自身 & LAM
- `portal_admin`（门户 BFF 客户端，实际登录走门户 BFF，不一定需要列）——评审确认。
- LAM（external）保持独立登录 `lam/adminpass`，不入 SSO。

## 6. 改造点（文件级，实施清单）

| # | 位置 | 改动 |
|---|---|---|
| 1 | `Authentication/backend/app/seed.py` | SEED_USERS 改为带前缀账号；`demo_systems` 收紧为"该系统已开通"（严格白名单）；display_name 保留中文 |
| 2 | `Authentication/ldap/seed.ldif` | LDAP uid 同步带前缀；`displayName/cn` 中文 |
| 3 | 各系统 SSO 收口 | **剥本系统前缀 → 查本地账号；无本地账号 → 403 明确报错（替换 get_or_create）** |
| 3a | `TaskManager/backend/api/unified_auth.py` / `EventManager/backend/api/unified_auth.py` | 方式二收口：前缀剥离 + 无本地即拒（或白名单） |
| 3b | `CloudManager` GatewayAuthentication / `WorkFlowCenter` GatewayAuthentication | 方式一收口：对 `X-Auth-Username` 剥前缀查本地，无则 403 |
| 3c | `PermissionCenter` `GatewayTrust` | 方式一收口：剥前缀（`iam_`→本地），无则拒绝 |
| 3d | `ReleaseManager` `oidc_client.py`/`views.py` | 方式三收口：`uid` 剥 `release_` → 查本地；无则 403（不再 get_or_create 空用户） |
| 4 | 认证中心 `sso-url` / 门户分组 | 门户登录下拉按新账号；应用卡片仍指向各系统 SSO 入口 |
| 5 | `deploy/server/.env.server` | 若需要，注入各系统前缀常量（供收口使用，默认内置） |
| 6 | 清理 | 移除各系统被 SSO 静默建出的垃圾用户（如 workflow 的 zhangsan/lisi） |

> 实施后验证：admin 在每系统均为超管（工单可见流程测试）；张三仅经 `release_zhangsan` 进发布系统并见支付线数据；门户各分组只见该系统账号；未开通系统登录 → 403 提示。

## 7. 评审结论（已确认）

1. ✅ 前缀命名 `release_ / workflow_ / cloud_ / cmdb_ / event_ / iam_` 通过。
2. ✅ 各系统账号清单：Release 暂按 §5.1 四个演示账号（后续微调）；TaskManager/EventManager 各 1 个（`cmdb_wangwu` / `event_ops_user`）并收口白名单；Cloud/WorkFlow/IAM 按 §5.2~5.4。
3. ✅ LAM 保持 external 独立登录（`lam/adminpass`），不入 SSO。
4. ⏳ 实施时顺带清理已静默创建的空账号（如工单库 zhangsan/lisi、非清单用户）。
5. ⚠️ 待确认：Cloud 本地本名 `cloud_admin` 已天然唯一，是否仍套前缀变 `cloud_cloud_admin`（文档暂按"一律前缀"，实施时可特判保留）。
