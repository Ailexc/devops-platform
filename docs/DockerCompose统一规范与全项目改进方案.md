# Docker Compose 统一规范与全项目改进方案

> 状态：待评审  
> 范围：全部 9 个 compose 文件 + 相关 seed/settings + 4 个 Traefik 实例  
> 缘起：Authentication LAM 跳转地址事故（详见 `Authentication/docs/15-DockerCompose复盘与改进方案.md`），排查发现同类问题遍布所有项目，且各项目标准不一

---

## 一、全项目扫描结果

### 1.1 compose 文件 × 问题矩阵

| 项目 / 文件 | orb.local 出现 | 形式 | 自带 Traefik | 硬编码 ALLOWED_HOSTS | 综合评级 |
|---|---|---|---|---|---|
| `Authentication/docker-compose.yml` | 15 | `${VAR:-orb.local}` 默认值 + labels | ✅ v3.2（遗留） | 否 | 🔴 最差 |
| `WorkFlowCenter/docker-compose.yml` | 3 | **硬编码不走变量** + labels | ❌ | ✅ **完全硬编码** | 🔴 最差 |
| `TaskManager/docker-compose.yml` | 8 | `${ALLOWED_HOSTS:-*,...,orb.local...}` 默认值 + labels | ❌ | 否 | 🟠 |
| `EventManager/docker-compose.yml` | 8 | 同上 + labels | ❌ | 否 | 🟠 |
| `EventManager/docker-compose.go.yml` | 3 | labels | ✅ v3.0（遗留） | 否 | 🟠 |
| `ReleaseManager/docker-compose.yml` | 6 | `${VAR:-orb.local}` 默认值 + labels | ❌ | 否 | 🟠 |
| `PermissionCenter/deploy/docker-compose.yml` | 7 | 仅 labels + 注释 | ✅ v3.1.2（**PEP 组件，合理**） | 否 | 🟡 |
| `CloudManager/docker-compose.prod.yml` | 2 | `${CORS:-...,orb.local}` 默认值 | ❌ | 否 | 🟡 |
| `infra/gateway/docker-compose.yml` | 6 | 仅 labels（网关正主） | ✅ v3.7（**统一入口**） | 否 | 🟢 |

### 1.2 四个 Traefik 的裁决

| 实例 | 容器名 | 端口 | 裁决 | 理由 |
|------|--------|------|------|------|
| infra/gateway | devops-gateway | 8088-8099 | ✅ **保留，唯一路由网关** | 所有浏览器流量的统一入口 |
| PermissionCenter | iam-traefik | 18080 等 | ✅ **保留，重新定位注释** | 它不是路由网关，是 IAM Demo 的 **PEP 执行点**（forwardAuth → `/v1/gateway/check`），属架构组件；但需加注释防止后人误判为"又一个路由网关" |
| Authentication | authentication-gateway | 28001/8004/28080 | ❌ **退役** | Mac 单机 Demo 遗留；dynamic.yml 路由指向本 compose 不存在的服务；功能已被统一网关全覆盖（8095/8096/8097/8098/8099） |
| EventManager go 栈 | cmdb-event-go-traefik | 8082 | ❌ **退役** | 本地 Demo 遗留；go 后端现经前端 nginx `/go-api/` 反代 + 统一网关访问，无浏览器直连需求 |

### 1.3 其他发现

| # | 发现 | 位置 |
|---|------|------|
| 1 | `Authentication/backend/app/seed.py` 全套 orb.local 兜底（双份事实来源） | seed.py:70-106 |
| 2 | `Authentication/backend/app/config.py` issuer 默认 `auth.devops.orb.local` | config.py:24 |
| 3 | WorkFlowCenter `ALLOWED_HOSTS` 完全硬编码，无 `${VAR}` 插值 → 服务器上直接 IP 访问 API 会被 Django 拒绝（目前靠 nginx 容器名反代侥幸工作） | docker-compose.yml:23 |
| 4 | 端口冲突靠"挪高位端口"解决的历史痕迹：`28001 避开 aianytra-api`、`28081 避开 aianytra-admin` | Authentication / TaskManager 注释 |
| 5 | `.env.local` / `.env.cloud` 缺 `APP_URL_LAM`（server 有） | deploy/* |
| 6 | compose 中无硬编码 IP（干净 ✅，仅注释残留 114.55） | — |

---

## 二、统一规范（7 条，全项目一个标准）

> 判据只有一条：**文件跨平台，配置跟环境走。**

| # | 规范 | 内容 |
|---|------|------|
| **R1** | 浏览器可达 URL 一律环境变量 | compose 默认值只允许 `localhost:<port>`；**禁止 orb.local / 公网 IP 作为默认值**。容器间通信继续用 service name（现状已做对，保持） |
| **R2** | ALLOWED_HOSTS / CORS 通配兜底 | Demo 级项目默认 `${VAR:-*,localhost}`；显式白名单只写在 `.env.<env>` |
| **R3** | OrbStack labels 移出 base | 全部 `dev.orbstack.domains` 移入 `docker-compose.orbstack.yml`（Mac 开发叠加）；Linux 上零噪音 |
| **R4** | Traefik 只有两个 | infra/gateway（路由）+ iam-traefik（PEP，注释明确定位）；Authentication / EventManager-go 自带实例退役 |
| **R5** | 单一事实来源 | seed/settings 只读环境变量，兜底 `localhost`；`.env.<env>` 是唯一配置点 |
| **R6** | .env 全覆盖 | 每个浏览器可达变量在 local/server/cloud 三份 env 中**必须齐全**，缺项=部署缺陷 |
| **R7** | 不再挪端口 | 端口冲突统一在 `docs/端口分配.md` 里裁决并更新 infra 网关，禁止在项目 compose 里私开高位端口绕开 |

---

## 三、分项目改动清单

### 3.1 Authentication（最重，~2h）

| 文件 | 改动 |
|------|------|
| `docker-compose.yml` | ① 所有 `${VAR:-...orb.local...}` → `${VAR:-localhost:<port>}`；② 删除 traefik 服务块（含 28001/8004/28080）；③ 删除全部 dev.orbstack.domains labels |
| `gateway/`（整个目录） | 删除（dynamic.yml 引用不存在的服务，遗留物） |
| `backend/app/seed.py` | 兜底值统一 `localhost:<port>`；redirect_uris 派生保持跟随 env |
| `backend/app/config.py` | issuer 兜底改 `localhost`（仅签名 iss 字段，验签方 verify_aud=False 不受影响，需回归验证） |
| 新增 `docker-compose.orbstack.yml` | 承接全部 orbstack labels（Mac 开发 `-f docker-compose.yml -f docker-compose.orbstack.yml up`） |
| `Makefile` / `scripts/compose.sh` | 增加 orbstack 叠加逻辑（ENV=local 时自动叠加）+ `make ldap` 命令 |
| `deploy/local/.env.local` / `.env.cloud` | 补 `APP_URL_LAM` |

### 3.2 WorkFlowCenter（最简单但最危险，~0.5h）

| 文件 | 改动 |
|------|------|
| `docker-compose.yml` | `ALLOWED_HOSTS=api.workflow.orb.local,...` → `ALLOWED_HOSTS=${ALLOWED_HOSTS:-*,localhost}`（R2）；labels 移出 |

> ⚠️ 此项修复后服务器行为**变好**：目前直接 `http://192.168.3.155:8091/api/...` 若被 Django 拒绝属潜伏 bug，通配兜底后消除。

### 3.3 TaskManager / EventManager / ReleaseManager（同模式，各 ~1h）

| 文件 | 改动 |
|------|------|
| 各自 `docker-compose.yml` | ① `${ALLOWED_HOSTS:-*,...,orb.local...}` → `${ALLOWED_HOSTS:-*,localhost}`；② `${VAR:-orb.local}` → `${VAR:-localhost:<port>}`；③ labels 移出 |
| `EventManager/docker-compose.go.yml` | ① 删除 traefik 服务块（8082）；② labels 移出 |
| `deploy/local/.env.local` / `.env.cloud` | 核对补齐各项目浏览器可达变量 |

### 3.4 PermissionCenter（~0.5h，谨慎）

| 文件 | 改动 |
|------|------|
| `deploy/docker-compose.yml` | ① labels 移出；② iam-traefik **保留**，头部注释改写："PEP 执行点（IAM 架构组件），非路由网关，勿与 infra/gateway 混淆" |

### 3.5 CloudManager（~0.5h）

| 文件 | 改动 |
|------|------|
| `docker-compose.prod.yml` | `${CORS_ALLOWED_ORIGINS:-...,orb.local}` → `${CORS_ALLOWED_ORIGINS:-http://localhost:8090}`；`${DJANGO_ALLOWED_HOSTS:-...}` → 通配兜底 |

### 3.6 infra（~0.5h）

| 文件 | 改动 |
|------|------|
| `infra/gateway/docker-compose.yml` | labels 移入 `docker-compose.orbstack.yml`（网关本身不动） |
| `docs/端口分配.md` | 更新：移除 28001/28080/8004/8082，标注退役端口 |

---

## 四、实施顺序

| 阶段 | 内容 | 预估 | 风险 |
|------|------|------|------|
| **P1** | 低风险清理：TaskManager / EventManager / ReleaseManager / CloudManager 默认值统一 + labels 迁移 | 2h | 低（默认值路径，env 覆盖行为不变） |
| **P2** | WorkFlowCenter ALLOWED_HOSTS 修复 | 0.5h | 低（行为变好） |
| **P3** | Authentication 全套（compose 默认值 + seed + 退役 Traefik + orbstack override + Makefile） | 2h | 中（Traefik 退役需回归 8095-8099 链路） |
| **P4** | PermissionCenter 注释定位 + labels 迁移 | 0.5h | 低（traefik 本体不动） |
| **P5** | infra labels 迁移 + 端口文档更新 + 三环境端到端验证 | 1h | — |

**验证门禁**（每个阶段完成必测）：

```bash
# 1. 全仓库禁止项扫描必须为 0
grep -rn "orb.local" --include="docker-compose*.yml" . | grep -v orbstack.yml   # 期望空
# 2. 服务器端到端：门户登录 → 六系统卡片跳转 → 各系统 me 接口 200
# 3. 兜底验证：注释掉任一 APP_URL_* 后启动 → 默认 localhost 可达（不再拿到死域名）
```

---

## 五、一句话结论

**9 个 compose 文件，9 套默认值标准**：Authentication 混搭、WorkFlowCenter 硬编码、TaskManager/Event/Release 把 orb.local 塞进通配兜底、CloudManager 塞进 CORS、PermissionCenter 最干净。统一成一套规范（R1-R7）后：**compose 描述结构，env 描述环境，OrbStack 只是 Mac 的可选项**——换服务器、回 Mac、上公有云，都只动 `deploy/<env>/.env.<env>` 一个文件。
