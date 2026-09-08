# CMDB 任务管理平台 — Go Backend

> 基于 Python (Django+Celery) 版本的 Go 重写，前端复用、同一 API 契约、可一键切换演示。

## 技术栈

| 组件 | 选型 | 版本 |
|------|------|------|
| Web 框架 | Gin | v1.9+ |
| ORM | GORM | v1.25+ |
| 数据库迁移 | golang-migrate | v4 |
| 任务队列 | asynq | v0.24+ |
| Redis | go-redis/v9 | v9 |
| AWS SDK | aws-sdk-go-v2 | v1 |
| 校验 | go-playground/validator | v10 |
| 断路器 | sony/gobreaker | v2 |
| 日志 | slog (标准库) | Go 1.21+ |
| 配置 | viper | v1 |

## 快速开始

### 前置条件

- Go 1.22+
- PostgreSQL 15+
- Redis 7+

### 启动

```bash
# 1. 创建数据库
createdb cmdb_go

# 2. 设置环境变量
export DB_DSN="postgres://cmdb:cmdb_dev@localhost:5432/cmdb_go?sslmode=disable"
export REDIS_ADDR="localhost:6379"
export REDIS_DB=1

# 3. 编译并运行
cd go-backend
go build -o bin/cmdb-server ./cmd/server
./bin/cmdb-server --role=all

# 或直接运行
go run ./cmd/server --role=all
```

### Docker

```bash
cd go-backend
docker build -t cmdb-go-backend .
docker run -p 8080:8080 \
  -e DB_DSN="postgres://cmdb:cmdb_dev@host.docker.internal:5432/cmdb_go?sslmode=disable" \
  -e REDIS_ADDR="host.docker.internal:6379" \
  -e REDIS_DB=1 \
  cmdb-go-backend
```

### 与 Python 版共存

```yaml
# docker-compose.yml 中新增
go-backend:
  build: ./go-backend
  command: server --role=all --port=8080
  environment:
    DB_DSN: postgres://cmdb:cmdb_dev@db:5432/cmdb_go
    REDIS_ADDR: redis:6379
    REDIS_DB: "1"
  ports:
    - "8080:8080"
```

## API 端点（24 个，与 openapi.json 对齐）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Dashboard | GET | `/api/v1/dashboard/stats/` | 大盘摘要 |
| | GET | `/api/v1/dashboard/workers/` | Worker 池状态 |
| | GET | `/api/v1/dashboard/resource-health/` | 模块健康度 |
| | GET | `/api/v1/dashboard/task-trend/` | 7 天趋势 |
| | GET | `/api/v1/dashboard/health-ranking/` | 健康排行 |
| | GET | `/api/v1/dashboard/current/` | 当前执行中 |
| | GET | `/api/v1/dashboard/recent-events/` | 最近事件 |
| | GET | `/api/v1/dashboard/resource-breakdown/` | 资源构成 |
| | GET | `/api/v1/dashboard/aws-resources/` | AWS 资源树 |
| Tasks | GET | `/api/v1/tasks/tree/` | 任务树 |
| | POST | `/api/v1/tasks/execute/` | 下发同步 |
| | PUT | `/api/v1/tasks/schedule/` | 设置/取消 cron |
| | GET | `/api/v1/tasks/locks/` | 并发锁 |
| | POST | `/api/v1/tasks/preview/` | 预览 Diff |
| | POST | `/api/v1/tasks/test/run/` | 运行测试任务 |
| | GET | `/api/v1/tasks/test/status/{task_id}/` | 测试任务状态 |
| | GET | `/api/v1/tasks/test/file/` | 预览测试文件 |
| Config | GET | `/api/v1/config/regions/` | 区域配置 |
| | PUT | `/api/v1/config/regions/` | 更新区域配置 |
| | GET | `/api/v1/config/accounts/` | 账号列表 |
| History | GET | `/api/v1/history/` | 历史列表 |
| | GET | `/api/v1/history/{record_id}/` | 历史详情 |
| | POST | `/api/v1/history/{record_id}/retry/` | 一键重试 |
| Docs | GET | `/api/v1/docs/` | 文档列表 |
| | GET | `/api/v1/docs/{filename}` | 文档内容 |

## 契约验证

```bash
chmod +x scripts/contract_check.sh
./scripts/contract_check.sh http://localhost:8080
```

## 目录结构

```
go-backend/
├── cmd/server/main.go          # 入口
├── internal/
│   ├── config/                  # 配置 + DB/Redis 连接
│   ├── model/                   # GORM 模型
│   ├── api/                     # Gin 路由 + Handlers
│   ├── service/                 # 业务逻辑层
│   ├── orchestrator/            # 两波次编排状态机
│   ├── worker/                  # 异步任务处理器
│   ├── pkg/                     # 共享包（锁/生命周期/结果等）
│   ├── transform/               # 资源字段转换
│   └── resource/                # 资源定义（EC2/VPC/RDS）
├── migrations/                  # SQL 迁移文件
├── scripts/                     # 工具脚本
├── Dockerfile
├── Makefile
└── go.mod
```

## 开发里程碑

- [x] M1: 骨架与契约
- [ ] M2: 主链路 API
- [ ] M3: 编排与 Worker
- [ ] M4: 完整性打磨
- [ ] M5: 性能对比与文档
