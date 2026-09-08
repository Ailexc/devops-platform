# Go 版后端整体设计方案与开发计划

> 文档版本：v0.1（待 Review）
> 创建时间：2026-08-03
> 状态：**设计方案评审中，未开始实施**
> 关联文档：`plans/celery-async-concurrency-plan.md`

---

## 📋 目录

1. [背景与目标](#背景与目标)
2. [总体架构设计](#总体架构设计)
3. [技术选型](#技术选型)
4. [目录结构](#目录结构)
5. [API 契约设计](#api-契约设计)
6. [数据模型设计](#数据模型设计)
7. [核心机制设计](#核心机制设计)
8. [Worker 设计](#worker-设计)
9. [Test Lab 模块设计](#test-lab-模块设计)
10. [Docs 模块设计](#docs-模块设计)
11. [前端切换机制设计](#前端切换机制设计)
12. [部署设计](#部署设计)
13. [风险与对策](#风险与对策)
14. [开发计划](#开发计划)
15. [验收标准](#验收标准)
16. [面试叙事要点](#面试叙事要点)
17. [待 Review 决策点](#待-review-决策点)

---

## 背景与目标

### 背景

- 当前系统为 Python 实现：**Django + django-ninja**（API 层）+ **Celery + RabbitMQ**（Worker 层）
- 架构被新领导否决，计划迁移到 Go
- 为面试准备：**前端复用**（React，零改动），实现**完整 Go 后端**，并支持**前端一键切换 Python / Go 两个后端进行演示与 A/B 对比**
- 本方案只动后端与部署编排，**前端 API 契约完全不变**

### 目标

| # | 目标 | 衡量标准 |
|---|---|---|
| 1 | 完整的 Go 后端 | 前端 19 个接口全部可用，行为与 Python 版一致 |
| 2 | 前端可切换演示 | 运行时切换 API 后端，无需重新构建前端 |
| 3 | 体现架构设计 | 可插拔 Worker 抽象、状态机、幂等、重试/DLQ 全部实现 |
| 4 | 性能提升可量化 | 提供 A/B 基准数据（吞吐 / P99 延迟 / 资源占用） |
| 5 | 部署简化 | Go 栈仅需 PostgreSQL + Redis（Python 栈为 PG + Redis + RabbitMQ） |

### 非目标

- 不重写前端
- 不引入微服务 / K8s（保持 Compose 级 Demo 复杂度）
- 不做用户认证系统（原系统也没有）

---

## 总体架构设计

### 系统拓扑（双栈并存）

```
                        ┌──────────────────────────────────────────────┐
                        │              React 前端 (复用)               │
                        │  运行时切换 API_BASE（localStorage）          │
                        └───────┬───────────────────┬──────────────────┘
                                │                   │
              ┌─────────────────▼──┐   ┌────────────▼──────────────────┐
              │  Python 栈 (profile)│   │  Go 栈 (profile)             │
              │  py-api            │   │  go-api (Gin)                 │
              │  + py-worker       │   │  + go-worker (asynq)          │
              │  (Celery/RabbitMQ) │   │  + go-seed / go-tasklab       │
              └────┬─────────┬─────┘   └────┬─────────┬───────────────┘
                   │         │              │         │
              ┌────▼───┐ ┌───▼───┐    ┌────▼───┐ ┌───▼────┐
              │postgres│ │ redis │    │postgres│ │ redis  │
              │(py)    │ │ rabbit│    │(go)    │ │        │
              └────────┘ └───────┘    └────────┘ └────────┘
```

- 两套栈通过 **Docker Compose profile** 隔离（`python` / `go`），各自独立数据库
- 前端通过运行时配置切换 `API_BASE`，实现同一页面实时对比

### 核心链路（与 Python 版一一对应）

```
API 接收 → 创建 Event(pending) → 写 RECEIVED 日志 → 投递任务队列(asynq)
  → Worker 消费 → SELECT ... FOR UPDATE 行锁 + 幂等检查
  → registry.Resolve(event_type) 模式匹配路由（通配符）
  → Handler.Handle() → onSuccess / onFailure
  → 失败: 指数退避重试(max_retries=5) → 耗尽进 DLQ
```

---

## 技术选型

| 层次 | Python 现状 | Go 选型 | 备选 | 选型理由 |
|---|---|---|---|---|
| Web 框架 | django-ninja | **Gin** | Echo / Fiber | 生态最大、中间件丰富、文档全 |
| ORM | Django ORM | **GORM** | sqlc / ent / sqlx | 开发效率高、内置行锁、迁移生态 |
| 迁移 | Django makemigrations | **golang-migrate** | goose / atlas | SQL 文件迁移，与 ORM 解耦 |
| 参数校验 | pydantic | **go-playground/validator** | — | 结构体 tag 校验，对标 pydantic |
| 任务队列 | Celery + RabbitMQ | **asynq (Redis)** | river(PG) / machinery | 内置重试/死信/监控，**免 RabbitMQ** |
| 配置 | django settings + dotenv | **envconfig + godotenv** | viper | 轻量，环境变量驱动 |
| 日志 | logging | **slog（标准库）** | zerolog / zap | Go 1.21+ 标准库，零依赖 |
| API 文档 | ninja 自动 OpenAPI | **swaggo** | 手写 OpenAPI | 复刻 /api/docs 的契约文档能力 |
| 测试 | pytest | **标准库 testing + testify** | — | — |

### Go 版本与依赖

```
Go 1.24+
github.com/gin-gonic/gin
gorm.io/gorm + gorm.io/driver/postgres
github.com/golang-migrate/migrate
github.com/go-playground/validator/v10
github.com/hibiken/asynq
github.com/joho/godotenv
github.com/redis/go-redis/v9
github.com/swaggo/swag
```

### 技术决策记录（面试可讲）

1. **为什么 asynq 而不是 machinery/river**：asynq 基于 Redis，内置指数退避重试、死信队列、任务调度与监控面板，是 Celery 功能最接近的 Go 方案；同时**省掉 RabbitMQ 依赖**，部署面更小。
2. **为什么 GORM 而不是 sqlc**：本项目查询复杂度中等（筛选/聚合），GORM 开发效率高，且 `clause.Locking` 原生支持 `SELECT FOR UPDATE`，与 Django `select_for_update` 语义对齐。
3. **为什么 golang-migrate**：与 ORM 解耦，SQL 文件可评审可回滚，也便于两套栈共享同一份 schema。

---

## 目录结构

```
backend-go/
├── cmd/
│   ├── api/main.go                  # HTTP API 入口 (Gin)
│   ├── worker/main.go               # asynq Worker 入口
│   └── seed/main.go                 # 数据初始化命令（对标 manage.py seed_data）
├── internal/
│   ├── config/                      # 环境配置加载
│   │   └── config.go
│   ├── model/                       # GORM 模型（与 Django 模型对齐）
│   │   ├── event.go                 # Event
│   │   ├── event_log.go             # EventLog
│   │   └── handler_config.go        # EventHandlerConfig
│   ├── repository/                  # 数据访问层
│   │   ├── event_repo.go
│   │   ├── event_log_repo.go
│   │   └── stats_repo.go            # 统计聚合查询
│   ├── api/                         # HTTP 层
│   │   ├── router.go                # 路由注册（19 端点）
│   │   ├── middleware/              # CORS / 日志 / 恢复
│   │   ├── dto/                     # 请求/响应结构（契约对齐）
│   │   └── handler/                 # 各资源 handler
│   │       ├── events.go
│   │       ├── stats.go
│   │       ├── handlers.go
│   │       ├── docs.go
│   │       └── testlab.go
│   ├── eventhandler/                # 事件处理器（对标 backend/handlers/）
│   │   ├── registry.go              # 注册表 + 模式匹配
│   │   ├── base.go                  # Handler 接口 + HandlerResult
│   │   ├── aws/
│   │   │   ├── ec2.go
│   │   │   ├── rds.go
│   │   │   └── s3.go
│   │   ├── webhook/
│   │   │   └── github.go
│   │   └── internal/
│   │       ├── echo.go
│   │       └── health.go
│   ├── worker/                      # asynq 任务层（对标 backend/workers/）
│   │   ├── tasks.go                 # 事件处理任务
│   │   ├── retry.go                 # 指数退避策略
│   │   └── dispatcher.go            # 分发抽象（预留双后端演示扩展点）
│   ├── tasklab/                     # Test Lab 任务（对标 demo_tasks.py）
│   │   ├── fast_task.go             # 快任务：API 爬取 + 词频统计
│   │   ├── slow_task.go             # 慢任务：报告生成 + 进度上报
│   │   └── status_store.go          # Redis 任务状态存储
│   └── docs/                        # 文档模块（读取 docs/ 目录 HTML）
│       └── service.go
├── migrations/                      # golang-migrate SQL 文件
│   ├── 000001_init.up.sql
│   └── 000001_init.down.sql
├── docs/                            # Go 栈自带文档（golang-architecture.html 等）
├── output/                          # Test Lab 产物目录（挂载卷）
├── Dockerfile                       # 多阶段构建（api/worker/seed 共用）
├── go.mod
├── go.sum
└── .env.example
```

> 注：**方案 A（每栈自带文档，物理隔离）已确认** —— Python 栈文档在 `backend/docs/`，Go 栈文档在 `backend-go/docs/`，互不共享、互不串扰，前端切换后端时文档内容同步切换。`output/` 产物目录同理按栈隔离。

---

## API 契约设计

### 契约来源

- **权威契约 = django-ninja 自动生成的 OpenAPI**（`http://<py-api>/api/docs/openapi.json`）
- 实施第 1 步：启动 Python 栈抓取该 spec 存档，作为 Go 实现的对照基准
- 前端 `src/api.ts` 的 TS 类型是第二重校验

### 端点清单（19 个，前端实际调用）

| # | 方法 | 路径 | 说明 | 关键响应 |
|---|---|---|---|---|
| 1 | GET | `/api/v1/events` | 列表（page/page_size/status/event_type/source/search/search_field） | `EventListResponse` |
| 2 | GET | `/api/v1/events/{id}` | 详情 | `Event` |
| 3 | GET | `/api/v1/events/{id}/logs` | 日志时间线 | `EventLog[]` |
| 4 | POST | `/api/v1/events` | 创建（**201**） | `Event` |
| 5 | POST | `/api/v1/events/{id}/retry` | 手动重试 `{force:false}` | `Event` |
| 6 | POST | `/api/v1/events/dlq/replay` | 批量回放 `{event_ids:[]}` | `{replayed:int}` |
| 7 | GET | `/api/v1/stats` | 概览 | `Stats` |
| 8 | GET | `/api/v1/stats/queues` | 队列深度 | `[{name,label,depth}]` |
| 9 | GET | `/api/v1/stats/workers` | worker 状态 | `{total,online,active_tasks,queued_tasks,workers[]}` |
| 10 | GET | `/api/v1/stats/throughput` | 24h 每小时吞吐 | `[{hour,total,completed,failed,other}]` |
| 11 | GET | `/api/v1/stats/recent-failures` | 最近失败 `?limit=` | `[{id,event_type,status,error_message,retry_count,max_retries,received_at}]` |
| 12 | GET | `/api/v1/handlers` | handler 配置 | `[{id,name,event_type_pattern}]` |
| 13 | GET | `/api/v1/handlers/event-types` | 事件类型元数据 | `[{category,icon,pattern,description,handler}]` |
| 14 | GET | `/api/v1/docs` | 文档列表 | `DocInfo[]` |
| 15 | GET | `/api/v1/docs/{filename}` | 文档 HTML（iframe，`text/html`） | HTML |
| 16 | GET | `/api/v1/test-lab/tasks` | 任务列表 | `DemoTask[]` |
| 17 | POST | `/api/v1/test-lab/trigger` | 触发任务 `{task_id,count}` | `TriggerResult` |
| 18 | GET | `/api/v1/test-lab/status/{id}` | 任务状态（轮询） | `TaskStatus` |
| 19 | GET | `/api/v1/test-lab/preview?filename=` | 产物预览 | `FilePreview` |

### 必须精确复刻的契约细节（易错点）

| 细节 | 值 | 说明 |
|---|---|---|
| 创建状态码 | **201** | ninja 语义，前端 `request()` 依赖 `res.ok` |
| 可空字段 | `processed_at`、`p99_duration`、`avg_duration` 为 `null` 而非缺省 | 前端 TS 类型 `string \| null` |
| 错误格式 | `{"detail": "..."}` | 前端 `throw new Error(err.detail)` |
| 时间格式 | ISO8601（`received_at` 等） | 前端直接展示 |
| `by_status` | `Record<string, number>` 键为状态字符串 | 不可漏键 |
| UUID 序列化 | **小写字符串**，非大括号形式 | `Event.id` / `trace_id` |
| 分页 | `page` 从 1 开始 | 前端页码语义 |
| 搜索 | `raw_payload__batch_id` 的 JSON 字段查询 | GORM 需用 `jsonb` 查询语法 |
| DLQ 回放 | 只回放 `status=dlq` 的事件 | 过滤条件必须一致 |
| 文档接口 | 文件名校验（禁路径穿越、仅 `.html`） | 安全行为对齐 |
| `search_field=all` | 多字段 OR 查询（id/event_type/resource_id/raw_payload.batch_id） | 查询逻辑对齐 |

---

## 数据模型设计

### Event（对标 `Event` 模型）

| 字段 | 类型 | 约束/说明 |
|---|---|---|
| id | UUID | 主键，默认随机 |
| event_type | string(128) | 索引 |
| source | string(64) | 索引 |
| detail_type | string(64) | 默认 "" |
| resource_id | string(256) | 默认 "" |
| raw_payload | jsonb | 默认 `{}` |
| status | string(32) | 索引，枚举见状态机 |
| trace_id | UUID | 索引 |
| retry_count | int | 默认 0 |
| max_retries | int | 默认 5 |
| handler | string(128) | 默认 "" |
| worker_id | string(64) | 默认 "" |
| error_message | text | 默认 "" |
| received_at | timestamptz | 自动，索引 |
| processed_at | timestamptz | 可空 |

GORM 关键映射：

```go
type Event struct {
    ID           uuid.UUID      `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
    EventType    string         `gorm:"size:128;index"`
    Source       string         `gorm:"size:64;index"`
    DetailType   string         `gorm:"size:64;default:''"`
    ResourceID   string         `gorm:"size:256;default:''"`
    RawPayload   datatypes.JSON `gorm:"type:jsonb"`
    Status       string         `gorm:"size:32;index"`
    TraceID      uuid.UUID      `gorm:"type:uuid;index"`
    RetryCount   int            `gorm:"default:0"`
    MaxRetries   int            `gorm:"default:5"`
    Handler      string         `gorm:"size:128;default:''"`
    WorkerID     string         `gorm:"size:64;default:''"`
    ErrorMessage string         `gorm:"type:text;default:''"`
    ReceivedAt   time.Time      `gorm:"autoCreateTime;index"`
    ProcessedAt  *time.Time
    Logs         []EventLog     `gorm:"foreignKey:EventID"`
}
```

### EventLog（对标 `EventLog`，append-only）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 自增主键 |
| event_id | uuid FK | 索引，级联删除 |
| action | string(32) | 枚举：received/enqueued/routed/processing/retrying/completed/failed/dlq/retry_manual/replayed |
| detail | jsonb | 默认 `{}` |
| created_at | timestamptz | 自动 |

### EventHandlerConfig（对标 `EventHandlerConfig`）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| name | string(128) | 唯一 |
| event_type_pattern | string(256) | 如 `aws.ec2.*` |
| handler_class | string(256) | 如 `EC2StateChangeHandler` |
| timeout | int | 默认 60 |
| max_retries | int | 默认 5 |
| is_active | bool | 默认 true |
| description | text | 默认 "" |
| created_at / updated_at | timestamptz | 自动 |

### 迁移文件

`migrations/000001_init.up.sql` 手写建表 SQL（含索引与枚举检查约束），与 Django 迁移产生的 schema 保持一致，保证两栈可共享同一份数据理解。

---

## 核心机制设计

### 1. 状态机

```
                    ┌──────────┐
                    │  pending │◀────────────┐
                    └────┬─────┘             │ retry / replay
                         │ worker 领取        │
                    ┌────▼─────┐             │
                    │processing│             │
                    └────┬─────┘             │
              ┌──────────┼──────────┐        │
              ▼          ▼          ▼        │
        ┌─────────┐ ┌────────┐ ┌────────┐   │
        │completed│ │ failed │ │  dlq   │───┘
        └─────────┘ └────────┘ └────────┘
                        │ retry 未耗尽 ──────┘
```

- 状态枚举常量：`pending / processing / completed / failed / dlq`
- 与 Django `EventStatus.TextChoices` 字符串值完全一致（前端依赖）

### 2. 幂等（对标 `select_for_update`）

```go
// 事务内行锁 + 状态校验，与 Django 语义对齐
err := db.Transaction(func(tx *gorm.DB) error {
    var event model.Event
    if err := tx.Clauses(clause.Locking{Strength: "UPDATE", Options: "NOWAIT"}).
        First(&event, "id = ?", eventID).Error; err != nil {
        return err // 不存在或锁冲突 → 直接返回
    }
    if event.Status == model.StatusCompleted {
        return ErrAlreadyProcessed // 已完成 → 跳过
    }
    event.Status = model.StatusProcessing
    event.WorkerID = workerID
    return tx.Save(&event).Error
})
```

### 3. 重试策略（对标 `calculate_exponential_backoff`）

```go
// 与 Python 版算法一致：base=4s, max=300s, 50-100% jitter
func BackoffDelay(attempt int, base, max float64, r *rand.Rand) time.Duration {
    d := math.Min(base*math.Pow(2, float64(attempt)), max)
    d *= 0.5 + r.Float64()*0.5
    return time.Duration(d * float64(time.Second))
}
```

- asynq 通过 `RetryDelayFunc` 注入该策略
- `retry_count` / `max_retries` 持久化在 Event 表（与 Python 版共享逻辑）

### 4. DLQ

- **asynq 原生死信**：任务重试耗尽 → 进入 `dead` 队列（可配 `Archive`）
- **数据库状态**：Event 置为 `dlq`，写 `DLQ` 日志（与 Python 版行为一致）
- **回放**：`POST /events/dlq/replay` 重置状态 → 重新入队（对应 Python 版）

### 5. 路由注册表（对标 `core/router.py`）

```go
type Registry struct {
    mu       sync.RWMutex
    handlers map[string]HandlerFactory // pattern → factory
}

// 模式匹配：filepath.Match 支持 * 和 ?，语义对标 fnmatch
func (r *Registry) Resolve(eventType string) (Handler, error) {
    if h, ok := r.handlers[eventType]; ok {
        return h(), nil
    }
    for pattern, h := range r.handlers {
        if ok, _ := filepath.Match(pattern, eventType); ok {
            return h(), nil
        }
    }
    return nil, ErrHandlerNotFound
}
```

- 注册顺序与 Python 版一致：精确匹配 → 通配符 → 兜底 `*` → EchoHandler
- Handler 并发安全：**每个事件 new 一个实例**（对标 `handler_cls()`）

### 6. Handler 接口（对标 `BaseEventHandler`）

```go
type Handler interface {
    Handle(ctx context.Context, event *model.Event) (HandlerResult, error)
}
type HandlerResult struct {
    Success bool
    Message string
    Data    map[string]any
}
```

- **Python 的 async 直接映射为 Go 的 goroutine 并发**——这是性能叙事核心
- `onSuccess` / `onFailure` 回调逻辑照搬（状态更新 + 日志写入）

### 7. 可观测性（`/stats/workers`）

| 能力 | Python 实现 | Go 实现 |
|---|---|---|
| worker 在线状态 | Celery `inspect.ping()` | asynq `Inspector` + Redis 心跳 |
| 活跃任务数 | Celery `inspect.active()` | asynq `Inspector.ListActiveTasks` |
| 排队任务数 | 查 DB pending 数 | 查 DB pending 数 + asynq 队列深度 |
| 并发数 | Celery pool 配置 | 启动参数（worker 自曝 `/metrics` 或写入 Redis） |

- 返回结构完全一致，前端无需改动
- asynq 自带 Web UI（`asynqmon`），可作为 Go 栈的运维展示亮点

---

## Worker 设计

### asynq 任务定义

```go
const (
    TypeProcessEvent = "event:process"
)

// 任务 payload —— 与 Python 版投递内容对齐（事件 ID）
type ProcessEventPayload struct {
    EventID string `json:"event_id"`
}

// API 侧投递（对标 process_event.delay(event_id)）
client.Enqueue(ProcessEventPayload{EventID: id}, asynq.MaxRetry(5), ...)
```

### Worker 处理流程（对标 `workers/tasks.py`）

```
消费任务
  → 事务内 SELECT FOR UPDATE + 幂等检查
  → 标记 processing + 写日志
  → registry.Resolve(event_type)
  → 写 ROUTED 日志
  → handler.Handle(ctx, event)（goroutine 内执行）
  → success: onSuccess（completed + 日志）
  → 失败: PermanentError → DLQ；TransientError → 重试（asynq 调度）
```

### 队列规划

| 队列 | 用途 | asynq 配置 |
|---|---|---|
| `events` | 事件处理（默认） | `asynq.Queue("events")` |
| `events.high` | 高优先级（预留） | 优先级 `10` |
| `tasklab` | Test Lab 任务 | 与事件隔离 |
| `dead` | 死信（asynq 内置） | 自动归档 |

### 双后端演示扩展点（加分项，可选）

`dispatcher.go` 定义 `Dispatcher` 接口，API 层只依赖接口：

```go
type Dispatcher interface {
    Dispatch(ctx context.Context, eventID string) error
}
```

- 实现 1：`AsynqDispatcher`（默认）
- 实现 2：`SyncDispatcher`（无 Redis 时同步执行，对标 Celery eager 降级）
- 这是"可插拔任务后端"架构设计的落点，面试可直接演示

---

## Test Lab 模块设计

对标 `backend/workers/demo_tasks.py` + `api/v1/test_lab.py`：

| 任务 | Python 行为 | Go 实现 |
|---|---|---|
| 快任务 `fast` | 调用 JSONPlaceholder API 爬取 → 提取字段 → 词频统计 → 写 JSON 文件 | `tasklab/fast_task.go`，用 `net/http` + goroutine 并发爬取 |
| 慢任务 `slow` | 读数据 → 清洗 → 统计 → 生成报告，实时进度上报 | `tasklab/slow_task.go`，进度写入 Redis |

### 状态上报机制（对标 Celery `AsyncResult`）

- Celery `update_state` → Go 侧任务将进度写入 Redis：`tasklab:progress:{task_id}`（JSON）
- `GET /test-lab/status/{id}` 轮询读取：
  - `asynq.Inspector.GetTaskInfo` → 任务级状态（pending/active/retry/dead）
  - Redis 进度 key → 进度信息（`PROGRESS`）
  - 产物文件存在性 → 推导 `SUCCESS`
- 返回值结构（`state/meta/result/event_ids`）与 Python 版完全一致

### 产物

- `output/` 目录（Docker 卷挂载），路径穿越防护逻辑照搬
- 快任务/慢任务都会创建 `Event` 记录（`source=test-lab`），与 Python 版一致，保证 Dashboard 联动

---

## Docs 模块设计

对标 `api/v1/docs.py`：

| 接口 | Go 实现 |
|---|---|
| `GET /docs` | 遍历 `docs/*.html`，提取 `<title>` / meta description → `DocInfo[]` |
| `GET /docs/{filename}` | 读文件返回 `text/html; charset=utf-8`；校验：仅 `.html`、禁 `/`、`\`、`..` |

- 正则提取标题/描述逻辑照搬（`regexp` 标准库）
- `modified_at` 格式 `YYYY-MM-DD HH:MM` 对齐

---

## 前端切换机制设计

### 现状

```ts
// api.ts —— 构建时定死
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
```

TestLab / EventDetail 也直接引用 `API_BASE`。

### 改造（最小侵入）

```ts
// 新增一个运行时配置模块
const BACKEND_KEY = 'backendMode'          // 'python' | 'go'

export function getApiBase(): string {
  const mode = localStorage.getItem(BACKEND_KEY) || 'python'
  return mode === 'go'
    ? 'http://go-api.event-management.orb.local/api/v1'   // Go 栈
    : '/api/v1'                                           // Python 栈（或 py-api 域名）
}

export function switchBackend(mode: 'python' | 'go') {
  localStorage.setItem(BACKEND_KEY, mode)
  window.location.reload()   // 简单可靠
}
```

- 将 `api.ts` / TestLab.tsx / EventDetail.tsx 中的 `API_BASE` 改为调用 `getApiBase()`
- 在 `Layout.tsx` 顶栏加一个下拉/开关（"Python 后端 / Go 后端"）
- **切换 = 换 base URL + reload，不改任何页面逻辑**

### CORS

- Go 后端（Gin）启用 CORS 中间件，允许 `frontend.*.orb.local` 来源
- Python 端由 Traefik 网关处理（现状不变）

---

## 部署设计

### Docker Compose（Go 栈，`docker-compose.go.yml` 或 profile）

```
services:
  go-postgres:  postgres:16-alpine（独立卷）
  go-redis:     redis:7-alpine
  go-api:       多阶段构建 → Gin，监听 :8000
  go-worker:    同一二进制，`/worker` 子命令
  go-seed:      启动时执行迁移 + seed（对标 migrate + seed_data）
```

### Dockerfile（多阶段）

```dockerfile
FROM golang:1.24 AS builder
WORKDIR /src
COPY backend-go/ .
RUN CGO_ENABLED=0 go build -o /bin/api ./cmd/api
RUN CGO_ENABLED=0 go build -o /bin/worker ./cmd/worker
RUN CGO_ENABLED=0 go build -o /bin/seed ./cmd/seed

FROM alpine:3.20
COPY --from=builder /bin/api /bin/worker /bin/seed /usr/local/bin/
COPY backend-go/docs/ /app/docs/
EXPOSE 8000
# 镜像体积预计 < 50MB（Python 版 > 500MB）
```

### Makefile 扩展

```
up-go:         docker compose -f docker-compose.go.yml up -d
down-go:       docker compose -f docker-compose.go.yml down
go-dev-api:    cd backend-go && go run ./cmd/api
go-dev-worker: cd backend-go && go run ./cmd/worker
go-seed:       cd backend-go && go run ./cmd/seed
bench:         go run ./cmd/bench   # A/B 压测脚本
```

### 本地开发

- Go API 监听 `:8001`（与前端 Vite proxy 对齐）
- 无 Redis 时走 `SyncDispatcher` 降级（对标 eager 模式），Demo 可离线运行

---

## 风险与对策

| 风险 | 等级 | 对策 |
|---|---|---|
| **API 契约漂移**（字段/状态码/可空性） | 高 | 以 OpenAPI spec 为基准实施；逐端点对照测试；前端逐页人工验证 |
| 复杂查询迁移（`raw_payload__batch_id` JSON 搜索、TruncHour 聚合） | 中 | GORM `jsonb` 语法 + 原生 SQL 兜底；对照 Python 结果校验 |
| Test Lab 状态机制无 Celery 等价物 | 中 | Redis 进度 key + asynq Inspector 组合方案（见上文） |
| 双栈同时运行的资源占用 | 低 | Demo 期按需启动单栈即可，不必同时跑 |
| UUID/JSON 序列化格式不一致 | 中 | DTO 层显式序列化 + 契约测试锁定 |
| Go 经验不足导致进度延迟 | 中 | 核心链路先行（API+Worker），TestLab/Docs 后置，可裁剪 |

---

## 开发计划

### 里程碑

| 阶段 | 内容 | 预估 | 产出 |
|---|---|---|---|
| **P0 契约冻结** | 抓取 Python 栈 OpenAPI spec 存档；核对前端 19 端点 | 0.5 天 | `backend-go/docs/api-contract-openapi.json` |
| **P1 骨架** | go mod、config、GORM 模型、迁移 SQL、seed 命令、Dockerfile | 1.5 天 | 可启动的空 API + 建表 + 数据初始化 |
| **P2 API 层** | 19 端点全部实现（DTO 对齐契约），CORS 中间件 | 3-4 天 | 前端可直连 Go API 查看数据 |
| **P3 Worker** | asynq 接入、状态机、幂等行锁、重试、DLQ、路由注册表 | 2-3 天 | 事件全链路（创建→处理→完成/失败/DLQ） |
| **P4 Handlers** | 6 个 Handler（EC2/RDS/S3/GitHub/Echo/Health） | 1-2 天 | 与 Python 版行为一致 |
| **P5 Test Lab** | 快/慢任务 + 状态上报 + 产物预览 | 1-2 天 | TestLab 页面可用 |
| **P6 Docs 模块** | 文档列表 + 内容渲染 | 0.5 天 | DocsDetail 可用 |
| **P7 前端切换** | 运行时 API_BASE + Layout 切换开关 | 0.5 天 | 一键切换演示 |
| **P8 部署联调** | Go 栈 Compose、Makefile、端到端验证 | 1 天 | 双栈可独立启动 |
| **P9 基准测试** | A/B 压测：吞吐 / P99 / 内存（同量级 seed 数据） | 1 天 | `bench/` 报告 |

**合计：约 12～16 个工作日（2.5～3 周，单人）**

### 关键路径与裁剪策略

```
P0 → P1 → P2 → P3 → P4（核心链路，不可裁剪）
                ↘ P5 → P6（可裁剪，不影响主体演示）
P2 完成后即可开始 P7（前端切换），与 P3-P6 并行
```

- **时间紧张时**：P5/P6 可后置，主体演示（事件流 + Dashboard + 切换）不受影响
- P9 基准测试是面试核心素材，**不建议裁剪**

---

## 验收标准

- [ ] 前端 19 个接口在 Go 后端全部可用，页面无报错
- [ ] 事件全链路：创建 → 处理 → completed；失败 → 重试 → DLQ；手动重试/回放可用
- [ ] 幂等验证：并发投递同一事件不重复处理
- [ ] 前端一键切换 Python/Go 后端，数据视图正确
- [ ] Test Lab 快/慢任务可触发、可查状态、产物可预览
- [ ] Docs 模块展示与 Python 版一致
- [ ] A/B 基准报告产出（吞吐 / P99 / 内存）
- [ ] Go 栈镜像体积 < 50MB，仅依赖 PG + Redis

---

## 面试叙事要点

1. **渐进式迁移（绞杀者模式）**：前端契约不变 → 后端整体替换 → 双栈并存灰度对比
2. **API 契约即接口**：以 OpenAPI spec 为契约基准，前端零改动
3. **可插拔任务后端**：`Dispatcher` 抽象 + asynq/Sync 双实现
4. **性能量化**：真实 A/B 数据（Go worker 吞吐/延迟/内存 vs Celery）
5. **并发模型**：Python async + eventlet → Go goroutine，讲清 why
6. **部署简化**：Go 栈少一个 RabbitMQ，镜像从 500MB+ → <50MB
7. **诚实边界**：承认 handler 业务代码需重写、Go 开发效率低于 Django 等短板

---

## 待 Review 决策点

| # | 决策 | 选项 | 建议 |
|---|---|---|---|
| 1 | Web 框架 | Gin / Echo / Fiber | **Gin**（生态最大） |
| 2 | ORM | GORM / sqlc / ent | **GORM**（开发效率） |
| 3 | 任务队列 | asynq(Redis) / river(PG) | **asynq**（免 RabbitMQ、功能全） |
| 4 | 双栈运行方式 | 同一 Compose 双 profile / 两个 Compose 文件 | **两个 Compose 文件**（隔离清晰） |
| 5 | 前端切换 | localStorage + reload / 运行时 config.json | **localStorage + reload**（最简单） |
| 6 | Test Lab 是否首批实现 | 首批 / 后置 | **后置**（可裁剪） |
| 7 | 是否实现 asynq Web UI | 是 / 否 | 可选加分项 |
| 8 | 是否立即开工 | 确认方案后按 P0→P9 推进 | — |

---

*文档结束 — 待 Review 确认后更新为 v1.0 并开始实施*
