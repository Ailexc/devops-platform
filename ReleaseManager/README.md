# 发布系统 Demo (ReleaseManager)

一个功能相对完整的发布系统 Demo：应用管理、发布流水线（CI/CD）、审批、灰度/蓝绿/滚动发布、回滚、权限、配置中心与知识库。使用本地 kind 集群模拟真实 K8s 部署，三种语言（Go / Node / Python）Demo 应用展示发布效果。

> 完整规格见 [SPEC.md](./SPEC.md)；权限模型演进与架构见 [permission_model_evolution_architecture.md](./permission_model_evolution_architecture.md)。

---

## 目录

- [架构与组件](#架构与组件)
- [快速开始（Docker 部署）](#快速开始docker-部署)
- [本地开发模式](#本地开发模式)
- [运维操作](#运维操作)
  - [一键重置（删除重建）](#一键重置删除重建)
  - [数据备份与恢复](#数据备份与恢复)
  - [常见故障排查](#常见故障排查)
    - [POST /api/v1/releases/ 500：deploy_mode NOT NULL](#post-apiv1releases-500deploy_mode-not-null)
    - [Demo 应用权限缺失（张三可见 / 李四不可见）](#demo-应用权限缺失张三可见--李四不可见)
  - [权限模型速览](#权限模型速览)
- [目录结构](#目录结构)

---

## 架构与组件

```
┌──────────────────────────────────────────────────────────────┐
│  React + Ant Design 前端（Nginx 反代 /api → backend）          │
│  frontend.release-system.orb.local                            │
└───────────────┬──────────────────────────────────────────────┘
                │ REST API (JWT)
┌───────────────▼──────────────────────────────────────────────┐
│  Django + DRF 后端（SQLite）                                  │
│  api.release-system.orb.local                                 │
└───────┬───────────────────────────────┬──────────────────────┘
        │ 服务间凭证(Ed25519)           │ HTTP
┌───────▼──────────────────────┐  ┌────▼──────────────────────────┐
│  Executor (FastAPI, :8765)   │  │ 本地 kind 集群 / Docker       │
│  executor.release-system...  │  │ demo-apps/（go/node/python）  │
└──────────────────────────────┘  └───────────────────────────────┘
```

| 组件 | 技术 | 域名 / 端口 |
|---|---|---|
| release-backend | Django 4.2 + DRF + SimpleJWT + SQLite | `api.release-system.orb.local` |
| release-frontend | React 18 + TS + Ant Design 5 + Nginx | `frontend.release-system.orb.local` |
| release-executor | FastAPI（模拟 spug-lambda 执行端） | `executor.release-system.orb.local` |
| release-init | 一次性初始化容器（密钥/迁移/种子） | 仅 `--profile init` 时运行 |

数据库使用 **SQLite**，存储于命名卷 `release-system_db-data`（挂载 `/app/data/db.sqlite3`）。

---

## 快速开始（Docker 部署）

依赖：Docker / OrbStack。

```bash
# 1. 构建并启动全部服务
docker compose up -d --build

# 2. 首次初始化（生成密钥 + 迁移 + 种子数据 + Demo 权限）
docker compose --profile init run --rm init

# 3. 访问
open https://frontend.release-system.orb.local
# 登录账号：选择 张三(zhangsan) / 李四(lisi) 等 Demo 账号（无密码）
```

**⚠️ 重要：命名卷与 `COMPOSE_PROJECT_NAME` 强绑定。** 项目改名/目录迁移后 Docker 会创建全新空卷，旧数据留在旧项目卷或仓库 `backend/db.sqlite3` 中。改名时请用 `docker compose --project-name <名> ...` 保持一致，或把旧卷数据复制到新卷（见[数据恢复](#数据备份与恢复)）。

---

## 本地开发模式

不依赖 Docker 的本地开发（Executor + Django + Vite）：

```bash
./init.sh    # 首次：迁移 + 种子数据 + Demo 权限
./dev.sh     # 启动后端(8000) + executor(8765) + 前端(5173)
```

> Demo 应用权限由 `init_seed` 的 `_ensure_demo_app_permissions()` 兜底处理（归属 payment-dev 组，张三/李四均可见），无需额外步骤。

---

## 运维操作

### 一键重置（删除重建）

无论当前数据处于什么状态，都可以用 `scripts/reset-all.sh` 恢复到**初始状态**（删除容器 + 数据卷后重建）：

```bash
./scripts/reset-all.sh              # 完整重置（含镜像重建，会二次确认）
./scripts/reset-all.sh -y           # 跳过确认
./scripts/reset-all.sh --no-build   # 不重建镜像（用现有镜像，更快）
```

脚本流程：

```
备份当前库 → down -v（删容器+删 db-data/shared-keys 卷）→ docker compose build
→ init（密钥/迁移/种子）→ up -d → 等待后端就绪 → 自动验证 Demo 应用对张三/李四可见
```

**注意：** 运行后系统回到初始状态（无发布历史），重置前会自动备份到 `.db-backups/reset-pre-<时间戳>.sqlite3`，需要时可用备份还原（见下）。

### 数据备份与恢复

**备份位置：** `.db-backups/`（重置/恢复前会自动生成快照）

| 文件 | 说明 |
|---|---|
| `reset-pre-<时间戳>.sqlite3` | 每次重置前自动备份 |
| `current-volume-db.sqlite3` | 运行卷快照 |
| `original-local-db.sqlite3` | 仓库 `backend/db.sqlite3` 的历史副本（含完整发布历史） |

**恢复发布历史（历史数据在仓库 `backend/db.sqlite3` 或备份中）：**

```bash
# 1. 停止后端
docker compose stop release-backend

# 2. 把历史库复制进运行卷（用备份文件替换 /data/db.sqlite3）
docker run --rm -v release-system_db-data:/data \
  -v "$PWD/.db-backups/original-local-db.sqlite3":/tmp/db.sqlite3:ro \
  alpine sh -c 'cp /tmp/db.sqlite3 /data/db.sqlite3 && chmod 644 /data/db.sqlite3'

# 3. 启动后端并补齐迁移（旧库可能缺少 0009 等新迁移）
docker compose up -d release-backend
docker exec release-backend python manage.py migrate
```

> 注：命名卷 ID（`release-system_db-data`）随 `COMPOSE_PROJECT_NAME` 变化，恢复前用 `docker volume ls | grep release` 确认。

### 常见故障排查

#### POST /api/v1/releases/ 500：deploy_mode NOT NULL

**现象：** 创建发布单报 `NOT NULL constraint failed: release.deploy_mode`（500）。

**根因：** 种子数据把应用的 `deploy_mode` 设为 `None`；创建发布时视图读 `app.deploy_mode` 得到 `None`，传给 `serializer.save(deploy_mode=None)` 覆盖了模型默认值 `'k8s'`，而 `release` 表该列是 `NOT NULL`。

**修复（已合入代码）：**
- `backend/apps/releases/views.py`：`deploy_mode = app.deploy_mode or 'k8s'`（兜底）
- `backend/apps/accounts/management/commands/init_seed.py`：种子 `deploy_mode='k8s'`
- `backend/apps/releases/management/commands/seed_releases.py`：同样兜底

**已有库修复：** 运行 `docker exec release-backend python manage.py init_seed`（幂等，会把应用 `deploy_mode` 修正为 `k8s`）后重建镜像重启。

#### Demo 应用权限缺失（张三可见 / 李四不可见）

**现象：** 3 个 Demo 应用（go-app/node-app/python-app）在发布管理里"又没了"——登录张三能看到，登录李四（Demo 应用负责人）看不到。

**根因：** 应用可见性由 `RoleDataRule` → `EffectivePermissionCache` 驱动，**owner 字段不授予可见性**。Demo 应用此前 `owner_group` 为空 → `_create_group_default_rules` 跳过 → 无组规则；而旧版 `init.sh` 把权限硬编码授予**张三个人规则**并删除 demo 全部规则，导致权限错位（张三可见、李四不可见）。

**修复（已合入代码）：**
- Demo 应用负责人统一为**李四**、归属 **payment-dev** 组（own_group 模型，组内张三/李四均可见）
- `init_seed.py` 新增 `_ensure_demo_app_permissions()`：强制 `owner_group=payment-dev` + 补齐组规则（dev/test 全环境，幂等），根治"初始化脚本没搞定"问题
- `init.sh` 移除旧的硬编码"张三个人规则"方案，避免与组规则冲突

**已有库修复：** `docker exec release-backend python manage.py init_seed` 后即可（会重建权限缓存）。

### 权限模型速览

- 可见性 = `RoleDataRule`（own_group 组内 / cross_group 协作）→ 有效权限缓存
- **owner 字段只用于审批归属/责任展示，不授予可见性**
- 组（Group）是授权主体：组内成员通过 `SubjectMembership` 继承组规则
- 修改权限后需重建缓存：`rebuild_user_cache(user)`（`init_seed` 末尾自动全量重建）

---

## 目录结构

```
backend/    Django 后端（apps: accounts/authz/releases/applications/...）
frontend/   React + TS + Ant Design 前端
executor/   FastAPI 执行端（模拟 spug-lambda，调用本地 kind/Docker）
demo-apps/  三个 Demo 应用（go/node/python）
k8s/        kind 集群部署脚本与 Demo 应用清单
scripts/    运维脚本（docker-init.sh / reset-all.sh / ...）
docs/       面试题等文档
plans/      各类设计与重构计划
.db-backups/ 数据库备份
```
