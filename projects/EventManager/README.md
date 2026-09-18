# EventFlow

一个基于 Python + Go 双栈架构的事件管理系统，支持多种事件源（AWS、GitHub Webhook、内部系统等）的统一处理和监控。

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                       前端 (React + Vite)                    │
│                  http://frontend.event-management.orb.local │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│        Python API           │   │          Go API             │
│   Django + Ninja + Celery   │   │      GORM + PostgreSQL      │
│   http://api.event...       │   │   http://api.go.event...    │
└─────────────────────────────┘   └─────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    基础设施                                   │
│   PostgreSQL │ Redis │ RabbitMQ │ Traefik │ Nginx            │
└─────────────────────────────────────────────────────────────┘
```

> **数据边界**：事件系统使用独立逻辑库（devops_event，共享 PG 实例、逻辑库隔离），与平台其它系统互不直读写——系统间只走平台网关 API + 统一认证 JWT。Demo 以本地 PostgreSQL 模拟，无外部数据源接入；事件是平台的“发生事实”记录源，本系统拥有自己的事件数据主权。

## 🚀 快速开始

### 一键初始化（推荐）

```bash
# 克隆项目
git clone <repo-url>
cd EventManager

# 一键初始化（自动检测环境，初始化 Python + Go 两个栈）
make init-all
```

### 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.12 | 后端运行环境 |
| Go | >= 1.19 | Go 后端运行环境 |
| Node.js | >= 18 | 前端构建 |
| Docker | 最新版本 | 容器化部署（可选） |
| PostgreSQL | >= 16 | Go 栈数据库 |
| Redis | >= 7 | 缓存和消息队列 |
| RabbitMQ | >= 3 | Celery 任务队列 |

### 本地开发

```bash
# 1. 安装 Python 依赖
cd backend && pip install -r requirements.txt && cd ..

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3. 执行数据库迁移
make migrate

# 4. 一键初始化数据（各1000条模拟事件）
make init-all

# 5. 启动开发服务器
make dev-backend   # Python API (端口 8000)
make dev-worker    # Celery Worker
make dev-frontend  # 前端 (端口 3000)
```

### Docker 部署

```bash
# 启动所有服务
make up

# 一键初始化数据
make init-all-docker

# 查看服务状态
make ps

# 查看日志
make logs
```

## 📊 数据初始化

EventFlow 提供了完整的一键初始化系统，可以快速搭建开发环境。

### 常用命令

| 命令 | 说明 |
|------|------|
| `make init-all` | 一键初始化（推荐，自动检测环境） |
| `make init-all-local` | 本地模式初始化（无 Docker） |
| `make init-all-docker` | Docker 模式初始化 |
| `make init-python` | 只初始化 Python 栈 |
| `make init-go` | 只初始化 Go 栈 |
| `make seed-all` | 快捷初始化（Docker 模式，各1000条） |

### 自定义初始化

```bash
# 生成 5000 条数据，先清空现有数据
./scripts/init-all.sh -t 5000 -c

# 只初始化 Go 栈，Docker 模式
./scripts/init-all.sh -s go -m docker

# 查看所有参数
./scripts/init-all.sh --help
```

### 初始化参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --total NUM` | 生成事件数量 | 1000 |
| `-c, --clear` | 清空现有数据后重新初始化 | false |
| `-m, --mode MODE` | 运行模式: auto, docker, local | auto |
| `-s, --stack STACK` | 初始化的栈: all, python, go | all |

### 初始化流程

```
用户命令 → Makefile → init-all.sh → Python/Go 种子脚本 → 数据库
```

**Python 栈：**
1. 执行 Django migrations 创建表结构
2. 运行 `seed_data` 命令生成模拟事件数据
3. 创建 EventLog 和 EventHandlerConfig

**Go 栈：**
1. GORM AutoMigrate 自动检查并补建表结构
2. 运行 `cmd/seed` 生成模拟事件数据
3. 创建 EventLog 和 EventHandlerConfig

### 事件模板

初始化脚本会生成 6 类事件模板的模拟数据：

| 事件类型 | 来源 | 完成率 | 失败率 | DLQ率 |
|---------|------|--------|--------|-------|
| AWS EC2 | aws | 75% | 10% | 5% |
| AWS RDS | aws | 80% | 8% | 4% |
| AWS S3 | aws | 85% | 5% | 2% |
| GitHub Webhook | github | 88% | 5% | 2% |
| Internal Health | scheduler | 98% | 1% | 0% |
| Echo Test | manual | 60% | 20% | 10% |

## 🛠️ 开发指南

### 项目结构

```
EventManager/
├── backend/                 # Python 后端 (Django)
│   ├── api/                 # API 路由和视图
│   ├── apps/                # Django 应用
│   │   └── event_store/     # 事件存储应用
│   ├── config/              # Django 配置
│   ├── core/                # 核心业务逻辑
│   └── handlers/            # 事件处理器
├── backend-go/              # Go 后端
│   ├── cmd/                 # 命令行入口
│   │   ├── api/             # API 服务
│   │   ├── seed/            # 种子数据
│   │   └── worker/          # Worker 服务
│   ├── internal/            # 内部包
│   └── migrations/          # 数据库迁移
├── frontend/                # 前端 (React + Vite)
├── scripts/                 # 初始化脚本
│   ├── init-all.sh          # 一键初始化脚本
│   ├── test-init.sh         # 脚本测试
│   └── demo.sh              # 功能演示
├── docker/                  # Docker 配置
└── Makefile                 # 构建命令
```

### 常用命令

```bash
# 服务管理
make up                    # 启动所有服务
make down                  # 停止所有服务
make restart               # 重启所有服务
make ps                    # 查看服务状态
make logs                  # 查看日志

# 开发模式
make dev-backend           # 启动 Python 开发服务器
make dev-worker            # 启动 Celery Worker
make dev-frontend          # 启动前端开发服务器

# 代码质量
make lint                  # 代码检查
make format                # 代码格式化
make test                  # 运行测试
make test-cov              # 测试覆盖率

# 数据库
make migrate               # 执行数据库迁移
make shell                 # Django shell
```

### 数据库配置

**Python 栈 (SQLite)**
- 数据库文件：`backend/db.sqlite3`
- 迁移命令：`cd backend && python manage.py migrate`
- 种子数据：`cd backend && python manage.py seed_data`

**Go 栈 (PostgreSQL)**
- 数据库名称：`eventdb_go`
- 端口：5433
- 迁移文件：`backend-go/migrations/000001_init.up.sql`
- 种子数据：`cd backend-go && go run ./cmd/seed`

## 🐳 Docker 部署

### 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 3000 | 前端应用 |
| api | 8000 | Python API |
| worker | - | Celery Worker |
| go-api | 8001 | Go API |
| go-worker | - | Go Worker |
| postgres | 5433 | PostgreSQL |
| redis | 6380 | Redis |
| rabbitmq | 5672 | RabbitMQ |

### 域名配置 (OrbStack)

```
http://frontend.event-management.orb.local → 前端
http://api.event-management.orb.local      → Python API
http://api.go-event-management.orb.local   → Go API
```

### Docker 命令

```bash
# 启动所有服务
docker compose up -d

# 启动特定服务
docker compose up -d api worker

# 查看日志
docker compose logs -f api

# 停止服务
docker compose down
```

## 📝 API 文档

### Python API

- 基础 URL：`http://localhost:8000/api/v1/`
- 事件列表：`GET /api/v1/events/`
- 事件详情：`GET /api/v1/events/{id}/`
- 创建事件：`POST /api/v1/events/`
- 统计数据：`GET /api/v1/stats/`

### Go API

- 基础 URL：`http://localhost:8001/api/v1/`
- 事件列表：`GET /api/v1/events/`
- 事件详情：`GET /api/v1/events/{id}/`
- 创建事件：`POST /api/v1/events/`

## 🔧 故障排除

### 常见问题

**1. Python 虚拟环境未激活**
```bash
source .venv/bin/activate
```

**2. PostgreSQL 未运行**
```bash
# macOS
brew services start postgresql

# Docker
docker compose up -d postgres
```

**3. 数据库迁移失败**
```bash
# 重新执行迁移
make migrate

# 或手动执行
cd backend && python manage.py migrate
```

**4. 种子数据初始化失败**
```bash
# 检查数据库连接
psql -h localhost -p 5433 -U eventuser -d eventdb_go

# 重新初始化
make init-all -c
```

**5. Docker 服务未启动**
```bash
# 检查服务状态
docker compose ps

# 重启服务
docker compose restart
```

### 日志查看

```bash
# Python API 日志
docker compose logs -f api

# Go API 日志
docker compose logs -f go-api

# 前端日志
docker compose logs -f frontend
```

## 📚 文档

- [初始化脚本使用指南](scripts/README.md)
- [初始化脚本使用示例](scripts/EXAMPLES.md)
- [初始化系统架构](scripts/ARCHITECTURE.md)
- [初始化系统总结](scripts/SUMMARY.md)

## 🤝 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- Django - Python Web 框架
- Go - 编程语言
- React - 前端框架
- Vite - 前端构建工具
- PostgreSQL - 数据库
- Redis - 缓存
- RabbitMQ - 消息队列
