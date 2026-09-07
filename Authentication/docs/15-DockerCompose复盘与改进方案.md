# Authentication docker-compose.yml 复盘与改进方案

> 状态：待评审  
> 范围：`Authentication/docker-compose.yml` 为主，兼评 `gateway/dynamic/dynamic.yml`、`seed.py`、`deploy/*/.env.*` 配置链路  
> 背景：服务器部署时发现 LAM 跳转地址仍是 OrbStack 域名，暴露出 compose 文件中环境相关配置的系统性问题

---

## 一、先回答问题

### 1.1 跳转地址到底以什么为主？

**以环境变量为主，compose 里的默认值只是"裸跑兜底"。**

加载链路：`make start` → `scripts/lib.sh load_env()` → 按 ENV 加载 `deploy/<env>/.env.<env>` → 变量注入 shell → docker compose 的 `${VAR:-default}` 插值。

三个环境的实际取值：

| 变量 | Mac (OrbStack) | 服务器 (.env.server) | 云端 (.env.cloud) |
|------|----------------|---------------------|-------------------|
| APP_URL_CLOUD_MANAGER | `http://cloud.devops.orb.local`（.env.local） | `http://192.168.3.155:8090` | 公网 IP:port |

### 1.2 默认值出现在 compose 里合理吗？

**机制合理，但当前默认值的"内容"不合理。** 问题不在"有没有默认值"，而在默认值本身是**平台相关的**：

- `http://cloud.authentication.orb.local` —— 只有 Mac + OrbStack 能解析，Linux 服务器上这是死地址
- `http://localhost:8083` —— Mac 上能通（端口映射），服务器上恰好也能通，但纯属巧合
- 两套平台的值混在同一份文件里，谁也不服谁

### 1.3 是不是不能跨平台、换平台就要改文件？

**现状：是。** 只要某平台的 `.env.<env>` 漏配某个变量（LAM 就是例子：`.env.local` / `.env.cloud` 至今没有 `APP_URL_LAM`），就会静默掉进 compose 默认值 → 服务器上拿到 orb.local 死地址。**故障模式是静默的**，这是最要命的一点。

**目标：不应该。** 改进后换平台只动 `deploy/<env>/.env.<env>`，compose 与代码零改动（见第四节）。

---

## 二、问题清单（按严重度）

### P1 🔴 compose 默认值混入平台相关地址

位置：`docker-compose.yml` L87-96

```yaml
- APP_URL_TASK_MANAGER=${APP_URL_TASK_MANAGER:-http://cmdb.devops.orb.local}      # orb.local
- APP_URL_LAM=${APP_URL_LAM:-http://localhost:8083}                                # localhost
- PORTAL_URL=${PORTAL_URL:-http://portal.authentication.orb.local}                 # orb.local
```

**危害**：默认值只在单一平台成立。任何环境漏配变量 → 静默拿到别的平台的死地址（LAM 事故根因）。

### P2 🔴 双 Traefik 网关并存，职责不清

- `authentication-gateway`（本 compose 自带，端口 28001/8004/28080）
- `devops-gateway`（infra 统一网关，端口 8088-8099，服务器实际入口）

本 compose 自带的 Traefik 是 Mac 单机 Demo 时代的产物。它的动态配置 `gateway/dynamic/dynamic.yml` 里路由指向 `cloud-manager-service` / `workflow-center-service` / `permission-center-service` —— **这些服务根本不在本 compose 里定义**（跨项目耦合，历史遗留）。服务器上它完全多余，还占用 8004 端口与统一网关的 pilot-app 入口重叠。

### P3 🟠 OrbStack 专属 label 写死在 base 文件

```yaml
labels:
  - "dev.orbstack.domains=ldapadmin.${COMPOSE_PROJECT_NAME:-authentication}.orb.local"
```

Linux 上被忽略（无害但误导），Mac 上生效。这是**平台特有配置**，不应出现在平台无关的 base 文件里。

### P4 🟠 seed.py 与 compose 各持一份默认值（双份事实来源）

`seed.py` 的 `_home_url("lam", "http://ldapadmin.authentication.orb.local")` 与 compose 的 `${APP_URL_LAM:-...}` 是两套独立兜底。谁先生效取决于调用路径，一旦两边改得不一致，排查成本翻倍。

### P5 🟡 .env 覆盖不全

- `.env.local` 无 `APP_URL_LAM`
- `.env.cloud` 无 `APP_URL_LAM`
- 本次服务器 LAM 地址错误 = `.env.server` 有、但 compose 无插值入口（已修）+ local/cloud 仍缺（未修）

### P6 🟡 端口体系混乱

| 端口 | 归属 | 备注 |
|------|------|------|
| 8002 | auth-backend 直连 | 本地调试用，服务器上裸露 |
| 8003 | direct-app | 统一网关 8096 与之重复 |
| 8005 | oidc-demo | 统一网关 8098 与之重复 |
| 8083 | LAM | 服务器实际使用 ✅ |
| 28001/28080 | 自带 Traefik | 与统一网关完全重复 |
| 8088-8099 | 统一网关 | 唯一事实入口 |

`# 云端改高位端口避开 aianytra-api(8001)` 这类注释是端口冲突史的直接证据——每次冲突靠"再挪一个高位端口"解决，而不是收敛入口。

### P7 🟢 profiles 机制用得好但不够显性

`profiles: ["ldap"]` 是正确的按需启动设计，但启动命令没进 Makefile（本次是手工 `docker compose --profile ldap up -d`），知识只存在于文件注释里。

---

## 三、设计原则（改进的判据）

1. **容器间通信 = service name**（如 `LDAP_SERVER_URI=ldap://openldap:389`）—— 天然可移植，这是本文件做对的部分，保持。
2. **浏览器可达 URL = 环境变量**，compose 不携带任何平台相关默认值。默认值只允许 `localhost:<port>`（所有平台都成立的最后兜底）。
3. **平台特有能力**（OrbStack labels）放 override 文件，不进 base。
4. **单一事实来源**：seed.py 只读环境变量不设平台默认值；`.env.<env>` 是唯一配置点。
5. **入口唯一**：所有浏览器流量走统一网关，项目自带 Traefik 退役。

---

## 四、改进方案

### 方案 A：最小修正（推荐，~0.5 天）

| # | 改动 | 文件 |
|---|------|------|
| A1 | 所有 `orb.local` 默认值改为 `localhost:<port>` | `docker-compose.yml` |
| A2 | 删除自带 traefik 服务及其 dynamic.yml（统一网关已全覆盖 mock/pilot/direct/oidc/auth-api） | `docker-compose.yml`、`gateway/` |
| A3 | OrbStack labels 移入 `docker-compose.orbstack.yml`（Mac 开发时 `-f ... -f ...override` 叠加） | 新文件 |
| A4 | seed.py 兜底值改为 `localhost:<port>`，与 compose 对齐 | `seed.py` |
| A5 | `.env.local` / `.env.cloud` 补齐 `APP_URL_LAM` | `deploy/*` |
| A6 | Makefile 增加 `make ldap`（`docker compose --profile ldap up -d`） | `Makefile` |

**效果**：换平台只改 `.env.<env>`；漏配变量时兜底是 localhost（至少本机可访问，且 fail 行为可预期），不再静默拿到别的平台的死域名。

### 方案 B：compose 分层（更彻底，~1-2 天）

```
docker-compose.yml            # 纯结构：服务、网络、依赖、容器间 env（service name）
docker-compose.ports.yml      # 所有 ports 映射（本地调试才叠加）
docker-compose.orbstack.yml   # OrbStack labels（Mac 才叠加）
deploy/<env>/.env.<env>       # 所有浏览器可达 URL + 密码
```

Makefile 统一封装叠加逻辑，开发者永远不需要知道叠加了哪几层。

**取舍**：B 更干净但改动面大、验证成本高；A 解决了全部实际痛点，B 可以等 A 稳定后再演进。

### 目标形态示例（方案 A 后的 LAM 段）

```yaml
lam:
  image: ldapaccountmanager/lam:stable
  profiles: ["ldap"]
  container_name: authentication-lam
  environment:
    - LAM_PASSWORD=${LDAP_ADMIN_PASSWORD:-adminpass}
    - LDAP_SERVER=ldap://openldap:389        # 容器间通信：service name，可移植
  ports:
    - "8083:80"                              # 本地直连兜底；服务器走统一入口或直连 IP:8083
```

浏览器可达地址完全由 env 决定：

```bash
# .env.server
APP_URL_LAM=http://${SERVER_IP}:8083
# .env.local（Mac）
APP_URL_LAM=http://localhost:8083
```

---

## 五、实施清单

| 阶段 | 任务 | 预估 | 风险 |
|------|------|------|------|
| 1 | A1 + A4 + A5（默认值统一 localhost、seed 对齐、env 补齐） | 1h | 低：仅改兜底值，env 覆盖路径不变 |
| 2 | A2（退役自带 Traefik） | 1h | 中：需确认 Mac 本地 Demo 流程不依赖 28001/8004 |
| 3 | A3 + A6（labels 迁移 + Makefile ldap 命令） | 1h | 低 |
| 4 | 端到端验证（Mac local / 服务器 各一轮） | 1h | — |

## 六、验证清单

| # | 验证项 | 预期 |
|---|--------|------|
| 1 | 服务器 `make start P=auth` 后门户 LAM 卡片跳转 | `http://192.168.3.155:8083` |
| 2 | Mac `ENV=local make start P=auth` 后 LAM 跳转 | `http://localhost:8083` |
| 3 | 任何环境故意删掉 `APP_URL_LAM` 再启动 | 兜底为 localhost:8083，本机可访问（不再拿到 orb.local 死地址） |
| 4 | 退役自带 Traefik 后 mock/pilot/oidc-demo 全链路 | 统一网关 8095/8097/8098 正常 |
| 5 | `grep orb.local docker-compose.yml` | 0 结果 |

---

## 七、一句话结论

这份文件的**骨架（profiles、service name 通信、${VAR:-default} 机制）是对的**，烂在**兜底默认值里写死了 Mac 的地址、双网关并存、两份事实来源**。按方案 A 修完后，"换个服务器改一次文件"和"回 Mac 改回去"这两件事都不再存在——改的永远只是 `.env.<env>`。
