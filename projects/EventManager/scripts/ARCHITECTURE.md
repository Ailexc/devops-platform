# 初始化系统架构

## 概述

EventFlow 项目实现了一套完整的数据初始化系统，支持 Python 和 Go 两个后端栈的统一初始化。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    初始化入口                                │
├─────────────────────────────────────────────────────────────┤
│  make init-all          ← 一键初始化（推荐）                  │
│  make init-all-local    ← 本地模式                           │
│  make init-all-docker   ← Docker 模式                        │
│  make init-python       ← 只初始化 Python                    │
│  make init-go           ← 只初始化 Go                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              scripts/init-all.sh                            │
│  统一初始化脚本（支持参数化配置）                               │
├─────────────────────────────────────────────────────────────┤
│  • 环境检测（auto/docker/local）                             │
│  • 依赖检查                                                  │
│  • 参数解析                                                  │
│  • 多栈初始化                                                │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│        Python 栈            │   │          Go 栈               │
├─────────────────────────────┤   ├─────────────────────────────┤
│ 1. Django Migration         │   │ 1. GORM AutoMigrate         │
│    • 创建表结构              │   │    • 自动创建表结构          │
│    • 执行迁移文件            │   │    • 检查并补建缺失表        │
│                              │   │                             │
│ 2. Seed Data Command        │   │ 2. Seed Data Command        │
│    • python manage.py        │   │    • go run ./cmd/seed      │
│      seed_data              │   │                             │
│    • 生成模拟事件数据        │   │    • 生成模拟事件数据        │
│    • 创建 EventLog          │   │    • 创建 EventLog          │
│    • 创建 EventHandlerConfig│   │    • 创建 EventHandlerConfig│
│                              │   │                             │
│ 3. 数据库: SQLite            │   │ 3. 数据库: PostgreSQL        │
│    backend/db.sqlite3       │   │    eventdb_go               │
└─────────────────────────────┘   └─────────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│        数据模板              │   │        数据模板              │
├─────────────────────────────┤   ├─────────────────────────────┤
│ 6 类事件模板：               │   │ 6 类事件模板：               │
│ 1. AWS EC2                  │   │ 1. AWS EC2                  │
│ 2. AWS RDS                  │   │ 2. AWS RDS                  │
│ 3. AWS S3                   │   │ 3. AWS S3                   │
│ 4. GitHub Webhook           │   │ 4. GitHub Webhook           │
│ 5. Internal Health          │   │ 5. Internal Health          │
│ 6. Echo Test                │   │ 6. Echo Test                │
│                              │   │                             │
│ 状态分布：                   │   │ 状态分布：                   │
│ • Completed: 75-98%         │   │ • Completed: 75-98%         │
│ • Failed: 1-20%             │   │ • Failed: 1-20%             │
│ • DLQ: 0-10%                │   │ • DLQ: 0-10%                │
│ • Processing: 0-5%          │   │ • Processing: 0-5%          │
│ • Pending: 0-5%             │   │ • Pending: 0-5%             │
└─────────────────────────────┘   └─────────────────────────────┘
```

## 组件说明

### 1. 初始化入口（Makefile）

提供用户友好的命令行接口：

```makefile
init-all          # 一键初始化（自动检测环境）
init-all-local    # 本地模式初始化
init-all-docker   # Docker 模式初始化
init-python       # 只初始化 Python 栈
init-go           # 只初始化 Go 栈
seed-all          # 快捷方式（Docker 模式，各1000条）
```

### 2. 统一初始化脚本（init-all.sh）

核心脚本功能：

- **环境检测**：自动识别 Docker 或本地环境
- **依赖检查**：验证 Python、Go、PostgreSQL 等依赖
- **参数解析**：支持自定义数据量、清空模式等
- **多栈初始化**：可同时或单独初始化 Python/Go 栈
- **错误处理**：完善的错误提示和故障排除

### 3. Python 种子数据（seed_data.py）

Django 管理命令：

```bash
python manage.py seed_data [选项]

选项：
  --total NUM    生成事件数量（默认 1000）
  --real NUM     走真实 API 处理的事件数
  --clear        先清空现有数据
```

功能特点：
- 批量写入（每批 100 条）
- 事务保证数据一致性
- 自动生成 EventLog
- 支持清空重置

### 4. Go 种子数据（cmd/seed/main.go）

独立 Go 程序：

```bash
go run ./cmd/seed

环境变量：
  SEED_TOTAL     生成事件数量（默认 1000）
  SEED_CLEAR     是否清空现有数据（true/false）
  DATABASE_URL   数据库连接字符串
```

功能特点：
- GORM AutoMigrate 自动建表
- 批量写入优化
- 与 Python 栈使用相同的数据模板
- 支持 Docker 容器化运行

## 数据流

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  用户执行    │    │  脚本解析    │    │  环境检测    │
│  make init   │ →  │  参数和选项  │ →  │  docker/local│
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
                                                ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  数据写入    │    │  种子数据    │    │  数据库迁移  │
│  PostgreSQL/ │ ←  │  生成事件    │ ←  │  创建表结构  │
│  SQLite      │    │  EventLog    │    │  执行迁移    │
└──────────────┘    │  Config      │    └──────────────┘
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  初始化完成  │
                    │  显示摘要    │
                    └──────────────┘
```

## 配置管理

### 环境变量

Python 栈：
```bash
DATABASE_URL=sqlite:///backend/db.sqlite3
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

Go 栈：
```bash
DATABASE_URL=postgres://eventuser:eventpass@localhost:5433/eventdb_go
REDIS_URL=redis://localhost:6379/0
SEED_TOTAL=1000
SEED_CLEAR=true
```

### 数据库配置

| 栈    | 数据库   | 主机       | 端口 | 数据库名     |
|-------|----------|------------|------|-------------|
| Python| SQLite   | 本地文件   | -    | db.sqlite3  |
| Go    | PostgreSQL| localhost | 5433 | eventdb_go  |

## 扩展性

### 添加新的初始化步骤

1. 在 `init-all.sh` 中添加新的函数
2. 在 `main()` 函数中调用
3. 更新 Makefile 添加新的命令

### 添加新的数据模板

1. 在 `seed_data.py` 或 `cmd/seed/main.go` 中添加模板
2. 定义事件类型和负载生成函数
3. 设置状态分布权重

### 支持新的数据库

1. 修改 `init-all.sh` 中的数据库检测逻辑
2. 更新种子数据脚本的数据库连接
3. 添加相应的迁移文件

## 性能优化

### 批量写入

- Python：每批 100 条，使用 `bulk_create`
- Go：每批 100 条，使用 `CreateInBatches`

### 事务处理

- Python：使用 `transaction.atomic()` 包裹批量操作
- Go：GORM 自动事务管理

### 索引优化

- 创建必要的索引加速查询
- UUID 主键使用 PostgreSQL 的 `gen_random_uuid()`

## 监控和日志

### 初始化日志

```bash
# 查看实时日志
make init-all 2>&1 | tee init.log

# Docker 模式查看容器日志
docker compose logs -f go-seed
```

### 性能监控

```bash
# 测量初始化时间
time make init-all

# 监控数据库大小
du -sh backend/db.sqlite3
psql -c "SELECT pg_size_pretty(pg_database_size('eventdb_go'));"
```

## 最佳实践

1. **开发环境**：使用 `make init-all` 快速初始化
2. **测试环境**：使用 `-t 5000 -c` 生成足够测试数据
3. **CI/CD**：使用 `-m docker` 确保环境一致性
4. **数据重置**：定期使用 `-c` 清空重置，避免数据膨胀
5. **性能测试**：逐步增加数据量，观察系统表现

## 故障恢复

### 数据损坏

```bash
# 重置 Python 栈
./scripts/init-all.sh -s python -c

# 重置 Go 栈
./scripts/init-all.sh -s go -c

# 完全重置
./scripts/init-all.sh -c
```

### 服务异常

```bash
# 重启所有服务
make restart

# 重新初始化
make init-all
```

## 未来改进

1. **增量初始化**：支持只补充缺失的数据
2. **并行初始化**：同时初始化两个栈，提高速度
3. **数据验证**：初始化后自动验证数据完整性
4. **回滚机制**：支持回滚到之前的初始化状态
5. **Web 界面**：提供可视化的初始化配置界面
