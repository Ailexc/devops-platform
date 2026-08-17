# 项目开发约定

## 构建与验证（重要）

- **完成内容后一律通过 OrbStack（docker compose）构建部署验证**，不本地启动 `go run` / `vite dev`，避免与其他项目（workflow/cloud_manager 等）端口冲突增加调试成本。

### 标准流程

```bash
# 1. 构建镜像（宿主机交叉编译 → docker build）
make backend-image        # iam-backend（iam-server / mock-cmdb / mock-identity / iam-agent）
make frontend-image       # iam-frontend（npm ci + build → nginx）

# 2. 部署 / 重启服务
docker compose -f deploy/docker-compose.yml up -d iam-server frontend

# 3. 种子数据（幂等；--reset 一键重置重建完整 demo 数据）
docker compose -f deploy/docker-compose.yml run --rm iam-server iam-server seed
docker compose -f deploy/docker-compose.yml run --rm iam-server iam-server seed --reset   # 或 make seed-reset

# 4. 全链路验证
bash scripts/demo.sh
```

### 访问面（OrbStack 原生域名为主，宿主机端口映射为备用）

| 服务 | 首选地址（OrbStack 域名） | 备用（宿主机端口映射） |
|------|---------------------------|------------------------|
| 管理台（前端） | https://frontend.permission-center.orb.local | http://localhost:18088 |
| iam-server（API + PDP） | https://api.permission-center.orb.local | http://localhost:18080 |
| Traefik 网关（PEP） | https://cmdb.permission-center.orb.local | http://localhost:19080 |
| mock-cmdb | （容器内服务，走网关） | http://localhost:18090 |
| mock-identity | （容器内服务） | http://localhost:18091 |
| iam-agent | （容器内服务） | http://localhost:19090 |
| PostgreSQL / Redis / OpenFGA | （容器内服务） | :15432 / :16379 / :18081-18082 |

> 说明：部署一律在 OrbStack（docker compose 容器），不存在本地 `go run` / `vite dev` 进程；
> 宿主机端口映射（localhost:8088 等）只是容器的端口发布，与本地启动无关；汇报访问地址时使用 **OrbStack 域名**。

### 例外

仅当需要临时调试且无法用容器复现时，才允许本地启动；用后立即清理，不得长期占用端口。

## 数据安全与一键初始化（重要）

- **数据位置**：业务数据在 Docker 命名卷 `permission-center_pgdata`（PostgreSQL，含 IAM + OpenFGA）、`permission-center_redisdata`（Redis），**不在容器内**。compose 已固定 `name: permission-center`，迁移目录不会换卷（历史教训：未固定前换目录会新建空卷导致数据"丢失"）。
- **⚠️ 严禁 `docker compose down -v`**（`-v` 会删除命名卷，数据直接丢失）。清理/迁移前先确认旧卷（`docker volume ls`），不要贸然 `docker volume prune`。
- **数据可重建**：本系统是 Demo，种子脚本是最终防线——数据丢了直接一键重建，无需手工恢复。

### 一键初始化 / 备份命令

```bash
make seed          # 幂等补齐 demo 数据（不删已有数据，可重复跑）
make seed-reset    # 一键重置：清空全部 demo 表（ID 从 1 重排）→ 按最新 seed 重建
make reset-all     # 从零到可用：build 前后端 → 启动 → seed-reset → demo.sh 全链路验证
make backup        # 备份 IAM 数据库 → backups/iam-<时间戳>.sql（含 --clean 便于直接恢复）
make restore       # 从备份恢复（默认最新）：make restore [FILE=backups/xxx.sql]
```
