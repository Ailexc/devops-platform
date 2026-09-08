# EventFlow 初始化脚本

## 概述

这些脚本提供了 EventFlow 项目的快速初始化能力，可以同时初始化 Python 和 Go 两个后端栈。

## 快速开始

### 一键初始化（推荐）

```bash
# 自动检测环境，初始化两个栈
make init-all

# 或者直接运行脚本
./scripts/init-all.sh
```

### 指定模式初始化

```bash
# 本地模式（无 Docker）
make init-all-local

# Docker 模式
make init-all-docker
```

### 单独初始化某个栈

```bash
# 只初始化 Python 栈
make init-python

# 只初始化 Go 栈
make init-go
```

## 脚本参数

`scripts/init-all.sh` 支持以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --total NUM` | 生成事件数量 | 1000 |
| `-c, --clear` | 清空现有数据后重新初始化 | false |
| `-m, --mode MODE` | 运行模式: auto, docker, local | auto |
| `-s, --stack STACK` | 初始化的栈: all, python, go | all |
| `-h, --help` | 显示帮助信息 | - |

### 示例

```bash
# 生成 5000 条数据，先清空现有数据
./scripts/init-all.sh -t 5000 -c

# 只在 Docker 模式下初始化 Python 栈
./scripts/init-all.sh -m docker -s python

# 只在本地模式下初始化 Go 栈
./scripts/init-all.sh -m local -s go
```

## 初始化流程

### Python 栈

1. **数据库迁移**：执行 Django migrations 创建表结构
2. **种子数据**：生成模拟事件数据（Event, EventLog, EventHandlerConfig）
3. **数据模板**：包含 AWS EC2/RDS/S3、GitHub Webhook、Health Check、Echo Test 等 6 类事件

### Go 栈

1. **自动迁移**：使用 GORM AutoMigrate 检查并补建表结构
2. **清空数据**：可选清空现有数据
3. **种子数据**：生成模拟事件数据，与 Python 栈使用相同的数据模板

## 环境要求

### 本地模式

- Python 3.8+（建议使用虚拟环境）
- Go 1.19+
- PostgreSQL（Go 栈需要）
- Redis（Python 栈需要）
- RabbitMQ（Python 栈 Celery 需要）

### Docker 模式

- Docker
- Docker Compose

## 常用命令

```bash
# 查看服务状态
make ps

# 查看日志
make logs

# 重启服务
make restart

# 停止服务
make down

# 启动 Python 开发服务器
make dev-backend

# 启动 Go 开发服务器
make go-dev-api
```

## 数据库信息

### Python 栈
- 数据库：SQLite（`backend/db.sqlite3`）
- 迁移命令：`cd backend && python manage.py migrate`
- 种子数据：`cd backend && python manage.py seed_data`

### Go 栈
- 数据库：PostgreSQL（`eventdb_go`）
- 迁移文件：`backend-go/migrations/000001_init.up.sql`
- 种子数据：`cd backend-go && go run ./cmd/seed`

## 故障排除

### Python 栈初始化失败

1. 检查虚拟环境是否激活：`source .venv/bin/activate`
2. 检查依赖是否安装：`pip install -r backend/requirements.txt`
3. 手动执行迁移：`cd backend && python manage.py migrate`

### Go 栈初始化失败

1. 检查 Go 是否安装：`go version`
2. 检查 PostgreSQL 是否运行：`pg_isready`
3. 检查数据库连接：`psql -h localhost -p 5433 -U eventuser -d eventdb_go`

### Docker 模式问题

1. 检查 Docker 服务：`docker ps`
2. 检查容器日志：`docker compose logs`
3. 重建镜像：`docker compose build --no-cache`

## 开发建议

1. **首次初始化**：推荐使用 `make init-all`，自动检测环境并初始化
2. **数据量控制**：开发环境建议 1000-5000 条，测试环境可增加到 10000+
3. **定期重置**：如需重置数据，使用 `-c` 参数清空后重新初始化
4. **环境隔离**：Python 和 Go 使用不同的数据库，可以独立初始化
