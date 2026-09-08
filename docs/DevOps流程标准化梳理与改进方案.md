# DevOps 流程标准化：现状梳理与改进方案

> 状态：已实施（2026-09-08，分支 fix/compose-unify-platform-neutral）  
> 范围：Makefile 全部命令、scripts/ 全部脚本、环境判定机制、部署双路径  
> 缘起：环境判定靠"猜"（env 文件存在性）、部署脚本与 make 路径数据初始化范围不一致

---

## 一、Makefile 命令全量梳理

### 1.1 命令清单（按用途分组）

#### ① 基础设施 / 环境

| 命令 | 背后脚本 | 作用 | 环境感知 |
|------|----------|------|----------|
| `make bootstrap` | `scripts/bootstrap.sh` | 启动统一 PG/Redis/RabbitMQ + 创建 10 个业务库 | load_env 自动检测 |
| `make env`（**无**） | — | ❌ 不存在：无法查看当前环境 | — |
| `make use E=xxx`（**无**） | — | ❌ 不存在：无法显式切换环境 | — |

#### ② 生命周期（核心）

| 命令 | 背后脚本 | 作用 |
|------|----------|------|
| `make start [P=xx]` | `scripts/start.sh` | **日常主入口**：确保 infra → OpenFGA migrate →（可选 reset）→ compose up。P 缺省=全部 7 项目 |
| `make up [P=xx]` | `scripts/compose.sh up` | 纯 compose up（不含 infra 检查/migrate），与 start 语义重叠 |
| `make down [P=xx]` | `scripts/compose.sh down` | 停止（保留数据卷） |
| `make build [P=xx]` | `scripts/compose.sh build` | 构建镜像 |
| `make reset [P=xx]` | `scripts/reset-all.sh` | 数据回到出厂态（DB 重建 + 逐项目种子 + Redis 清空） |
| `make seed [P=xx]` | `scripts/seed.sh` | 初始化演示数据（**覆盖不全**，见 1.3） |
| `make demo-reset` | `scripts/demo-reset.sh` | 演示一键恢复 = reset-all 全量硬重置（BUILD=1 先构建） |

#### ③ 观测 / 运维

| 命令 | 作用 |
|------|------|
| `make status` / `ps` | 基础设施 + 业务容器状态 |
| `make logs P=xx` | 单项目日志 |
| `make backup` | `scripts/backup.sh` 数据备份 |
| `make portal` | 打印门户地址（**有猜测问题**，见 1.4） |
| `make gateway-up/down/ps` | 统一网关起停/状态（generate-routes 生成路由） |
| `make ldap` | LDAP + LAM 启动（--profile ldap） |
| `make deploy-server` | `scripts/deploy-server.sh` 一键部署（见 1.5） |

### 1.2 Makefile 卫生问题

| # | 问题 |
|---|------|
| 1 | `.PHONY` 缺 `ldap`、`deploy-server` |
| 2 | `portal` 目标：无条件读 `deploy/server/.env.server` 的 SERVER_IP → **Mac 上全量 clone 后也会打印服务器地址**（猜法同病）；兜底还是写死的 orb.local |
| 3 | `start` 与 `up` 语义重叠，新用户不知用哪个 |
| 4 | 无 `env` / `use` 命令——环境是整个体系最关键的状态，却没有一等公民命令 |

### 1.3 数据初始化覆盖矩阵（核心矛盾）

| 初始化步骤 | make start | make seed | make reset | deploy-server.sh |
|-----------|:---:|:---:|:---:|:---:|
| infra + 建库 | ✅ | — | — | ✅（经 make bootstrap） |
| OpenFGA migrate | ✅ | — | ✅ | ✅（经 make start） |
| auth 认证中心种子 | ✅（容器启动时） | — | ✅ | ✅ |
| **IAM seed（用户/应用/授权）** | ❌ | ❌ | ✅（`--reset` 版） | ✅（独有 5.5） |
| **LDAP/LAM 拉镜像+启动** | ❌ | ❌ | ❌ | ✅（独有 5.6） |
| **Release init_seed + seed_releases** | ❌ | ❌ | 部分 | ✅（独有 5.7） |
| **Workflow seed_data** | ❌ | ✅ | ✅ | ✅（独有 5.8，多一个 seed_demo_data） |
| Workflow seed_demo_data | ❌（但容器 command 自带） | — | ✅ | ✅ |
| TaskManager seed_demo_data | ✅（容器 command 自带） | ✅ | ✅ | —（靠容器自启） |

**结论**：全新机器只跑 `make start`，门户里 LAM 卡片失效、IAM/Release 部分演示数据缺失；只有跑过 `deploy-server.sh` 才是"全的"。**同一个"部署完成"有两个标准**——这就是双路径不一致的实质。

### 1.4 环境判定现状（靠猜）

`load_env()`（scripts/lib.sh）四级判定：

```
1. 显式 ENV=xxx         ← 最优先，但日常没人带
2. 仓库路径 = /opt/DevOpsPlatform → cloud
3. deploy/server/.env.server 存在  → server   ← 全量 clone 的 Mac 也会命中！
4. deploy/cloud/.env.cloud 存在    → cloud
5. 兜底                      → local
```

**问题**：环境 = "仓库里恰好有哪个文件"，不是人的显式声明。回 Mac 开发忘加 `ENV=local` → 拿到服务器 IP 配置，且**无任何警告**。

---

## 二、scripts/ 清单与调用关系

```
Makefile
 ├─ bootstrap ────→ scripts/bootstrap.sh      （infra 起停 + 建库）
 ├─ start/up/build/down/logs ─→ scripts/compose.sh + start.sh
 │                    start.sh ─┬─ lib.sh load_env（环境判定）
 │                              ├─ bootstrap（infra 缺失时）
 │                              ├─ openfga migrate
 │                              └─ compose up（可选先 reset-all）
 ├─ seed ─────────→ scripts/seed.sh           （覆盖不全 ⚠️）
 ├─ reset ────────→ scripts/reset-all.sh      （出厂态，覆盖较全）
 ├─ demo-reset ───→ scripts/demo-reset.sh ───→ reset-all.sh
 ├─ backup ───────→ scripts/backup.sh
 ├─ gateway-* ────→ scripts/generate-routes.sh + infra/gateway compose
 ├─ ldap ─────────→ Authentication compose --profile ldap
 └─ deploy-server ─→ scripts/deploy-server.sh ─┬─ 自有 5.5~5.8 步骤 ⚠️（与上重复/独有）
                                                ├─ make bootstrap/start/gateway-up
deploy-cloud.sh（云上手工跑）                    └─ 验证段（与 server 版 90% 重复）
```

其他问题：

| # | 问题 | 位置 |
|---|------|------|
| 1 | deploy-cloud 与 deploy-server **90% 代码重复** | 两文件 |
| 2 | deploy 脚本 source lib.sh 后**重新定义 log/err/ok**（前缀 hack） | 两文件 |
| 3 | deploy-cloud 硬编码 Gitee 仓库地址 | deploy-cloud.sh:22 |
| 4 | deploy-server 硬编码 `GOARCH=amd64`，而 IAM compose 用 `${GOARCH:-amd64}`（env 驱动）——同一件事两种写法 | deploy-server.sh 步骤 3 |
| 5 | 脚本自身无统一入口测试/冒烟 | — |

---

## 三、改进方案

### 3.1 核心：环境显式声明（消灭"猜"）

**新增仓库根状态文件 `.env-active`**（内容一行：`local|server|cloud`，gitignore）：

```
load_env 判定顺序（改后）：
1. 显式 ENV=xxx                      ← CI/一次性覆盖
2. 仓库根 .env-active 文件           ← 人显式声明（新）
3. 兜底猜 + ⚠️ 大字警告              ← 仅首次使用
```

**新增 Makefile 命令**：

```makefile
make env          # 显示当前环境 + 关键地址（PORTAL_URL/SERVER_IP）
make use E=server # 切换环境：写 .env-active + 打印该环境关键信息
```

**未声明时的行为**（对应"弹出选择"）：
- 交互终端（`[ -t 0 ]`）：`select` 列出三个环境让用户选，选择后写入 `.env-active`
- 非交互（CI/脚本）：按旧逻辑兜底猜，但**打印醒目警告** `⚠️ 未声明环境，自动检测为 server（make use 可显式指定）`

### 3.2 数据初始化统一：preflight 下沉

新增 `scripts/preflight.sh`（全幂等，有则跳过），把 deploy-server.sh 独有的 5.5~5.8 收编：

```bash
scripts/preflight.sh:
  1. IAM seed（iam-server seed，非 --reset，幂等）
  2. LDAP/LAM 镜像确保（ensure_image 多源拉取）+ --profile ldap up
  3. Release init_seed + seed_releases
  4. Workflow seed_data + seed_demo_data
```

集成点：`make start`（全部启动时）末尾调用；`make seed` 升级为 preflight 的别名语义；`make ldap` 保留（单独起 LDAP 用）。

**效果**：`make start` 在全新机器上一步到位 = 过去 `deploy-server.sh` 的完整效果。**"部署完成"只剩一个标准。**

### 3.3 deploy 脚本合并瘦身

```
scripts/deploy.sh（唯一实现）:
  ① [云上] 可选 git pull
  ② ENV=<由 .env-active/参数决定> 
  ③ make bootstrap → make start → make gateway-up → 验证
scripts/deploy-cloud.sh / deploy-server.sh → 保留为 3 行薄壳（兼容旧习惯），
  仅差异：cloud = git pull + ENV=cloud；server = ENV=server
```

验证段抽成 `scripts/verify.sh` 共用；GOARCH 交给 env（`${GOARCH:-amd64}`），删硬编码。

### 3.4 Makefile 整理

| 改动 | 内容 |
|------|------|
| 补 `.PHONY` | ldap、deploy-server |
| `make env` / `make use E=xx` | 新增（3.1） |
| `portal` 修猜测 | 读 `.env-active` 对应 env 文件的 PORTAL_URL，兜底才猜 |
| `help` 分组 | 按 infra/生命周期/观测/部署 分组输出，不再一锅粥 |
| start/up 语义注释 | help 里写清：日常用 start；up = 跳过检查的裸 compose up |

### 3.5 不动的部分（明确边界）

- 各项目 compose（刚完成平台中立化，不在本次范围）
- reset-all.sh / demo-reset.sh 内部逻辑（已较完善）
- backup.sh / generate-routes.sh

---

## 四、执行计划

| 阶段 | 内容 | 预估 | 风险 |
|------|------|------|------|
| **E1** | `.env-active` + `make env/use` + load_env 改造（警告+交互选择） | 1h | 低（判定顺序向后兼容） |
| **E2** | `scripts/preflight.sh`（收编 5.5~5.8）+ make start/seed 集成 | 1h | 中（种子幂等性需逐项验证） |
| **E3** | `scripts/deploy.sh` 合并 + 两个旧脚本改薄壳 + verify.sh 抽取 | 1h | 中（deploy-server 现网路径，需回归） |
| **E4** | Makefile 整理（.PHONY/env/use/portal/help 分组） | 0.5h | 低 |
| **E5** | 双环境回归：服务器 `make start`（应自动 preflight）+ 模拟 Mac（ENV=local 干跑） | 1h | — |

**合计 ~4.5h**，全部在 `fix/compose-unify-platform-neutral` 分支续作或新开 `refactor/devops-flow-standard` 分支。

## 五、验证清单

| # | 验证项 | 预期 |
|---|--------|------|
| 1 | 服务器 `make env` | 显示 server + 192.168.3.155 |
| 2 | 删除 `.env-active` 后 `make start` | 交互 select（或非交互警告） |
| 3 | `make use E=local` 后 `make env` | local + localhost 地址 |
| 4 | 全新模拟（停 LDAP、清 IAM seed）后 `make start` | preflight 自动补齐 LAM 卡片/IAM 数据 |
| 5 | `make seed` | 等价于旧 deploy-server 5.5~5.8 效果 |
| 6 | `bash scripts/deploy-server.sh` | 行为与改前一致（薄壳转发） |
| 7 | `make portal` | 按 .env-active 打印对应地址 |

## 六、数据管理与"一键恢复到可演示状态"能力详解

### 6.1 数据平面：数据放在哪

| 层 | 载体 | 说明 |
|----|------|------|
| **业务数据** | 统一 PostgreSQL（devops-postgres 容器），**一实例 10 库** | `devops_auth / cloud / event / event_go / iam / openfga / release / cmdb / cmdb_go / workflow`——每项目独立库，互不穿透 |
| **缓存/队列态** | 统一 Redis，**按 DB index 隔离** | event=/2、workflow=/6、cmdb=/5、cmdb-go=/7……重置时按 index FLUSHDB |
| **文件态** | 命名卷 | `auth-keys`（JWT 密钥，**重置不清**）、`ldap-data/ldap-config`（LDAP 目录，仅 `reset.sh --full` 才清）、`output_data` 等 |
| **代码外状态** | 仓库内种子 | 各项目的 seed 命令 / entrypoint 内置种子 = "出厂态"的真正定义者 |

**设计判断**：一实例多库 + Redis 分 index + 密钥卷与数据卷分离——**数据平面本身是干净的**，重置天然可以按库精确爆破而不伤邻居。

### 6.2 一键恢复机制：三层结构（顶层编排 → 项目自机制 → 容器自种子）

**不是顶层直接写库覆盖，而是"顶层爆破数据层 + 分发到各项目自己的重建机制"的混合模式：**

```
make demo-reset / make reset
        │
        ▼
scripts/reset-all.sh（顶层编排，三阶段）
        │
        ├─ 阶段一：数据层出厂态
        │    DROP DATABASE ... WITH (FORCE) + createdb × 10 库
        │    Redis 按 index FLUSHDB
        │
        ├─ 阶段二：sidecar 迁移
        │    openfga migrate（run -T --rm）
        │    cmdb-go --force-recreate（--seed 自动迁移+播种）
        │
        └─ 阶段三：逐项目重置（case 分发到各项目"自己的机制"）
             auth     → Authentication/reset.sh（项目自有脚本；--full 连 LDAP 卷一起清）
             cloud    → 容器 entrypoint 自带 migrate+全套种子：只需 --force-recreate 拉起等就绪
             event    → EventManager/scripts/init-all.sh -c -t 1000（项目自有脚本）
             iam      → iam-server seed --reset（run --rm 一次性容器）
             release  → ReleaseManager/scripts/reset-all.sh -y（项目自有脚本，嵌套调用）
             cmdb     → 容器 command 自带 migrate+seed_demo_data：force-recreate + HTTP 探活
             workflow → drop_schema + api 重启 + manage.py reset_demo（migrate+flush+种子）
```

**项目层的三种风格并存**（关键发现）：

| 风格 | 项目 | 机制 |
|------|------|------|
| A. 容器自种子 | cmdb、cloud | 启动 command/entrypoint 自带 migrate+seed，重置=重建容器 |
| B. 项目自有 reset 脚本 | auth、event、release | 各自维护 reset.sh / init-all.sh / reset-all.sh |
| C. 显式 seed 命令 | iam、workflow | 顶层直接调 manage.py / 二进制 seed 子命令 |

### 6.3 工程质量：踩坑注释是真财富

reset-all.sh 内嵌的实战教训（都有对应防回归措施）：

| 坑 | 对策 |
|----|------|
| schema 清空后并发 migrate 触发 `pg_type_typname_nsp_index` 唯一约束竞态 | 禁止"清库后重复 exec migrate"，统一走容器重建 |
| 无 TTY 环境（nohup/管道）下 `docker compose run` 挂起 | `run -T` + `stdin </dev/null` |
| runserver stdout 块缓冲吞就绪日志 | 用 HTTP 探活代替日志关键字 |
| DB 重建后旧容器仍连旧 schema | `--force-recreate` 强制重启 |
| IAM 只建表不种子 → SSO 用户 401 | seed 步骤显式化 |

### 6.4 两种恢复模式

| 模式 | 命令 | 差异 |
|------|------|------|
| 快速恢复（默认） | `make demo-reset` | `NO_BUILD=1`：复用现有镜像，只重建数据（分钟级） |
| 完整恢复 | `make demo-reset BUILD=1` | 先重建最新镜像再重置（代码变更后用） |

---

## 七、整体架构规范能力评分

> 评分口径：每维 0-10 分，10 = 生产级规范；评分对象是"这套 monorepo 的工程化体系"，不是业务功能。

| 维度 | 得分 | 评语 |
|------|:---:|------|
| **数据平面设计** | **9** | 一实例多库 + Redis 分 index + 密钥/数据卷分离，边界清晰，重置可精确爆破。扣 1 分：LDAP 卷游离在统一编排外（profile + reset.sh --full 才覆盖） |
| **一键恢复体验** | **8** | demo-reset 快速/完整双模式实用；三阶段编排幂等且踩坑全部有对策注释。扣分：全量重置时长受逐项目串行限制 |
| **工程记忆（注释/文档）** | **8** | reset-all 的踩坑注释、compose 头部说明、docs/ 系列复盘——"为什么这么做"记录得非常完整，这是这套体系最值钱的部分之一 |
| **重置机制统一性** | **6.5** | 能力都在，但**三种项目风格并存**（自种子/自有脚本/显式命令），顶层 case 分发等于把"每项目怎么重置"的知识硬编码在顶层脚本里——新增项目要改两处 |
| **环境管理** | **4** | 靠 env 文件存在性猜 + /opt 路径魔法值 + 无 make env/use——全体系最弱一环 |
| **部署一致性** | **5** | make 与 deploy-* 双路径，数据初始化范围不一致（§1.3 矩阵），deploy 内部 90% 重复 |
| **平台中立性** | **6** | 本次 compose 统一化后大幅改善（R1-R7 落地），但 Mac 专属行为（OrbStack K8s demo、host.docker.internal）仍散布在代码层 |
| **总评** | **6.6 / 10** | **"单点能力优秀，体系一致性欠佳"**——每一个能力单拎出来都有模有样（数据平面、恢复、注释），但它们之间缺一套统一的"契约"：环境怎么声明、项目怎么声明自己的种子/重置接口、部署有几条路径。改进方向不是重写，而是**立契约** |

### 7.1 评价展开：好在哪、差在哪

**好的（要保持并发扬）**：
1. 踩坑即文档——每个坑在脚本里有因果注释和防回归措施，这在个人项目里罕见
2. 数据平面"一实例多库"的取舍正确——demo 规模下比每项目独立 PG 容器省资源且备份/重置原子
3. 恢复双模式（快速/完整）贴合"演示前 30 秒恢复"的真实需求

**差的（改进方案对号入座）**：
1. **环境声明缺失**（→ §3.1 `.env-active` + `make use`）
2. **项目无统一"重置契约"**（→ 新增建议，见 §8）
3. **部署双路径**（→ §3.3 deploy 合并 + preflight 下沉）

---

## 八、改进方案补充（数据维度）

### 8.1 新增：项目重置契约（约定优于配置）

现状三种风格 → 统一为一个约定：**每个项目根必须提供幂等的 `scripts/reset.sh`**（或 compose profile），顶层 reset-all 只做两件事：爆破数据层 + 调用统一契约。

```
约定契约（每项目实现其一，顶层不再 case 硬编码；统一收在 <Project>/scripts/ 目录）：
  <Project>/scripts/reset.sh   # 幂等完成本项目 migrate + seed + 就绪等待 + 自验证
顶层 reset-all.sh 阶段三简化为：
  for p in auth cloud event iam release cmdb workflow:
      drop_schema $db; ( cd $p && bash scripts/reset.sh )
```

收益：新增项目 = 实现 `scripts/reset.sh` 一个文件，顶层零改动；三种风格收敛为一种对外接口（内部爱怎么实现都行）；且消除了 ReleaseManager/scripts/reset-all.sh 与顶层同名脚本的混淆。

### 8.2 执行计划增补（并入 §四）

| 阶段 | 内容 | 预估 |
|------|------|------|
| E2.5 | 重置契约：7 个项目补齐/改造 `scripts/reset.sh`（auth/event/release 已有现成脚本改名收编） | 2h |
| E2.6 | reset-all.sh 阶段三改写为契约调用（删除 case 硬编码） | 0.5h |

### 8.3 落地记录（2026-09-08 实施完毕）

| 交付物 | 说明 |
|--------|------|
| `.env-active` + `make env` / `make use E=xx` | 环境显式声明；未声明时交互终端弹选择 / CI 打警告 |
| `load_env` 判定顺序 | 显式 ENV > .env-active > 兜底猜测（带警告） |
| 7 个契约 | `<Project>/scripts/reset.sh`（auth/event/release 收编现有脚本，其余新建） |
| `scripts/reset-all.sh` | 阶段三从 80 行 case 硬编码 → 契约循环；共享工具下沉 lib.sh |
| `scripts/preflight.sh` | 非破坏性演示数据确保（原 deploy-server 5.5~5.8 收编）；`make start` / `make seed` 共用 |
| `scripts/deploy.sh` + 薄壳 | deploy-server/deploy-cloud 90% 重复代码消除；GOARCH 改环境注入 |
| `scripts/ports.sh` | `make ports`：运行态端口映射（含范围映射）+ Traefik 路由 API；顺带修复 Dashboard 8086 误映射 |
| `scripts/menu.sh` | 裸 `make` 进入交互菜单；CI 非交互自动降级 help |
| Makefile | 命令面 17→10 一等 + 分组 help + .PHONY 补齐；默认目标 = 菜单 |
| 铁律 | 环境管参数，行为全平台一致；数据定义权在项目，编排权在顶层，接口是契约 |

---

## 九、一句话结论

**现状：环境靠猜、数据初始化有两条标准、deploy 脚本 90% 重复、Makefile 缺环境一等公民命令、项目重置三种风格并存。** 

**但这套体系的底子是好的**：数据平面设计干净（9 分）、一键恢复能力完整且踩坑全部文档化（8 分）——问题不在能力，在**缺契约**。改进后：`make use` 一处声明环境（所有命令跟随），`make start` 一步到位（preflight 自动补齐全部种子），每项目一个 `reset.sh` 契约（顶层零硬编码），deploy 脚本退化为薄壳——**make 是唯一入口，契约是唯一扩展点，deploy 只是它的快捷方式**。
