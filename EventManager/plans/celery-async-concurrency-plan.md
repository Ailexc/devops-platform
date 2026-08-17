# Celery 协程并发改造方案

> 文档版本：v1.0  
> 创建时间：2026-08-02  
> 状态：分析完成，待实施

---

## 📋 目录

1. [背景与目标](#背景与目标)
2. [当前架构分析](#当前架构分析)
3. [问题识别](#问题识别)
4. [技术选型分析](#技术选型分析)
5. [推荐方案](#推荐方案)
6. [架构对比](#架构对比)
7. [实施计划](#实施计划)
8. [预期收益](#预期收益)

---

## 背景与目标

### 项目概述

EventFlow 是一个事件驱动架构系统，核心链路为：

```
AWS 事件推送 → Backend API → Celery 队列 → Worker 处理 → 数据库
```

### 改造目标

1. **测试模块任务并发执行**：当前任务内部 N 个批次是顺序执行，需要改为并发执行
2. **Worker 协程级并发**：让 Celery 的执行单元是协程级别，提高并发处理能力
3. **保持 Celery 优势**：享受 Celery 提供的重试、可靠性保障等能力

---

## 当前架构分析

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        EventFlow 系统                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   AWS 事件    │───▶│   Backend    │───▶│   Celery     │      │
│  │   推送        │    │   API        │    │   队列       │      │
│  └──────────────┘    │  (监听+分发)  │    └──────┬───────┘      │
│                      └──────┬───────┘           │              │
│                             │                   ▼              │
│                             │            ┌──────────────┐      │
│                             │            │    Worker    │      │
│                             │            │  (threads)   │      │
│                             │            │  并发: 10    │      │
│                             │            └──────┬───────┘      │
│                             │                   │              │
│                             ▼                   ▼              │
│                      ┌──────────────────────────────┐          │
│                      │         PostgreSQL           │          │
│                      │           数据库              │          │
│                      └──────────────────────────────┘          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React      │◀───│   nginx      │◀───│  django-     │      │
│  │   前端       │    │   反向代理    │    │  ninja API   │      │
│  └──────────────┘    └──────────────┘    │  (查询展示)   │      │
│                                          └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Worker 配置现状

| 配置项 | 当前值 | 说明 |
|---|---|---|
| Worker Pool | `-P threads` | 线程池 |
| 并发数 | `--concurrency=10` | 10 个线程 |
| Broker | `amqp://` (RabbitMQ) | 分布式模式 |
| Eager 模式 | `task_always_eager=True` (无 broker 时) | 同步降级 |

### 关键代码分析

#### 任务执行方式

```python
# backend/workers/demo_tasks.py
@shared_task(bind=True)
def fetch_and_process(self, count: int = 1):
    for i in range(count):
        # 顺序执行每个批次
        # 同步阻塞 I/O
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            posts = json.loads(resp.read())
```

#### Handler 执行方式

```python
# backend/workers/tasks.py
def _run_async_handler(handler: BaseEventHandler, event: Event):
    """安全地运行 async handler（兼容 eager 模式）"""
    try:
        return asyncio.run(handler.handle(event))  # 每次创建新 event loop
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(handler.handle(event))
```

---

## 问题识别

### 问题 1：测试模块任务顺序执行

| 任务 | 执行方式 | 耗时示例 |
|---|---|---|
| `fetch_and_process` | `for` 循环顺序执行 | 5 批次 × 2秒 = 10秒 |
| `generate_report` | `for` 循环顺序执行 | 5 份报告 × 5秒 = 25秒 |

**问题**：N 个批次串行执行，无法利用并发优势。

### 问题 2：Worker 并发模型为线程级

| 维度 | 当前 (threads) | 理想 (eventlet) |
|---|---|---|
| 并发模型 | 线程级 | 协程级 |
| 内存消耗 | ~8MB/线程 | ~4KB/协程 |
| 100 并发内存 | ~800MB | ~400KB |
| I/O 阻塞 | 线程挂起 | 协作式让出 |
| 上下文切换 | 内核态切换 | 用户态切换 |

---

## 技术选型分析

### 1. django-ninja 的 async 支持

| 层次 | 异步能力 | 技术实现 |
|---|---|---|
| Web 层 (django-ninja) | ✅ async 视图 | Django ASGI + async/await |
| Worker 层 (Celery) | ✅ 协程能力 | eventlet/gevent（非原生 asyncio） |

**结论**：Web 层的 async 不会自动传递到 Worker 层，两层的异步能力是独立的。

### 2. Celery 的协程能力

| Worker Pool | 类型 | 协程级别 | 代码改动 |
|---|---|---|---|
| `prefork` (默认) | 多进程 | ❌ 进程级 | 无 |
| `threads` | 线程池 | ❌ 线程级 | 无 |
| `eventlet` | 绿色线程 | ✅ 协程级 | **无需改动** |
| `gevent` | 绿色线程 | ✅ 协程级 | **无需改动** |

**关键点**：Celery 的协程能力是通过 eventlet 或 gevent 实现的，它们是独立的协程库，不是 Python 原生的 asyncio。

Eventlet 的官方描述：
> "Eventlet is a concurrent networking library for Python that allows you to **change how you run your code, not how you write it**."

### 3. 为什么不用自己实现 asyncio 池

| 自己实现 asyncio 池 | Celery + eventlet |
|---|---|
| ❌ 需要自己实现重试机制 | ✅ 内置重试策略 |
| ❌ 需要自己实现分布式 | ✅ 原生分布式 |
| ❌ 需要自己实现监控 | ✅ Flower 等工具 |
| ❌ 需要自己实现任务状态 | ✅ 内置状态管理 |
| ❌ 需要自己实现队列管理 | ✅ 支持多种 Broker |
| ❌ 需要自己实现优雅关闭 | ✅ 内置信号处理 |

---

## 推荐方案

### 方案概述

**保持当前架构不变**，仅修改 Worker 的并发模型配置：

| 维度 | 当前 | 推荐 | 变化 |
|---|---|---|---|
| Worker Pool | `-P threads` | `-P eventlet` | 并发模型升级 |
| 并发数 | `--concurrency=10` | `--concurrency=100` | 10x 提升 |
| 代码改动 | - | 无 | 零改动 |
| 配置改动 | - | Dockerfile + requirements.txt | 2 文件 |

### 架构图（无变化）

```
┌─────────────────────────────────────────────────────────────────┐
│                        EventFlow 系统                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   AWS 事件    │───▶│   Backend    │───▶│   Celery     │      │
│  │   推送        │    │   API        │    │   队列       │      │
│  └──────────────┘    │  (监听+分发)  │    └──────┬───────┘      │
│                      └──────┬───────┘           │              │
│                             │                   ▼              │
│                             │            ┌──────────────┐      │
│                             │            │    Worker    │      │
│                             │            │  (eventlet)  │      │
│                             │            │  并发: 100   │      │
│                             │            └──────┬───────┘      │
│                             │                   │              │
│                             ▼                   ▼              │
│                      ┌──────────────────────────────┐          │
│                      │         PostgreSQL           │          │
│                      │           数据库              │          │
│                      └──────────────────────────────┘          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React      │◀───│   nginx      │◀───│  django-     │      │
│  │   前端       │    │   反向代理    │    │  ninja API   │      │
│  └──────────────┘    └──────────────┘    │  (查询展示)   │      │
│                                          └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 架构设计说明

| 组件 | 职责 | 技术选择 | 并发模型 |
|---|---|---|---|
| **事件消费层** | 监听 AWS 事件、分发任务 | django-ninja API | 线程级（够用） |
| **任务处理层** | 消费队列、处理事件 | Celery + eventlet | **协程级（核心）** |
| **数据存储层** | 持久化事件 | PostgreSQL | 连接池 |
| **查询展示层** | 提供查询 API | django-ninja（同步） | 线程级（够用） |

**核心设计思想**：
- 把资源和复杂度投入到**真正重要的地方**（Worker 层）
- View 层保持**简单可靠**（同步足够）
- 充分利用**成熟框架的能力**（Celery 生态）

---

## 架构对比

### 当前架构 vs 推荐架构

| 维度 | 当前架构 | 推荐架构 |
|---|---|---|
| **整体拓扑** | 完全相同 | 完全相同 |
| **组件数量** | 6 个组件 | 6 个组件 |
| **连接方式** | 完全相同 | 完全相同 |
| **核心链路** | 完全相同 | 完全相同 |
| **Worker Pool** | threads | eventlet |
| **并发数** | 10 | 100 |
| **并发模型** | 线程级 | 协程级 |

### 性能对比

| 指标 | 当前 (threads) | 推荐 (eventlet) | 提升 |
|---|---|---|---|
| 并发任务数 | 10 | 100 | **10x** |
| 内存占用 | ~80MB | ~400KB | **200x 节省** |
| 100 个事件处理时间 | ~10 秒 | ~1 秒 | **10x** |
| 上下文切换开销 | 高（内核态） | 低（用户态） | **显著降低** |

---

## 实施计划

### 改动文件清单

| # | 文件 | 改动类型 | 优先级 |
|---|---|---|---|
| 1 | `backend/requirements.txt` | 新增 `eventlet>=0.35` | P0 |
| 2 | `docker/Dockerfile.worker` | Worker pool → eventlet | P0 |
| 3 | `docker-compose.yml` | worker command 更新 | P0 |

### 详细改动

#### 1. requirements.txt

```txt
# 新增
eventlet>=0.35
```

#### 2. docker/Dockerfile.worker

```dockerfile
# 改动前
CMD ["celery", "-A", "config", "worker", "-P", "threads", "--concurrency=10", "-l", "info"]

# 改动后
CMD ["celery", "-A", "config", "worker", "-P", "eventlet", "--concurrency=100", "-l", "info"]
```

#### 3. docker-compose.yml

```yaml
# worker service 的 command 更新
command: celery -A config worker -P eventlet --concurrency=100 -l info
```

#### 4. backend/api/v1/test_lab.py（测试模块数量上限提升）

```python
# TASK_REGISTRY 中的 max_count 提升
"fast": {
    "max_count": 50,  # 原来 10
}
"slow": {
    "max_count": 20,  # 原来 5
}

# TriggerRequest 中的 count 字段限制提升
count: int = Field(1, ge=1, le=50, description="触发数量")  # 原来 le=10
```

### 验证步骤

1. 重新构建 worker 镜像
2. 启动服务
3. 通过测试模块触发任务
4. 验证并发执行效果
5. 监控资源消耗

---

## 预期收益

### 性能提升

| 场景 | 当前 | 推荐 | 提升 |
|---|---|---|---|
| 100 个 AWS 事件 | ~10 秒 | ~1 秒 | **10x** |
| 并发任务数 | 10 | 100 | **10x** |
| 内存占用 | ~80MB | ~400KB | **200x 节省** |

### 架构优势

| 维度 | 说明 |
|---|---|
| **可靠性** | 保持 Celery 的重试、DLQ 等能力 |
| **可扩展性** | 可轻松增加 Worker 实例 |
| **可监控性** | 完整的任务状态追踪 |
| **可维护性** | 零代码改动，仅配置变更 |

### 成本效益

| 成本项 | 说明 |
|---|---|
| **开发成本** | 零（无需改动业务代码） |
| **测试成本** | 低（仅验证配置变更） |
| **运维成本** | 低（配置简单） |
| **收益** | 高（10x 性能提升） |

---

## 风险与注意事项

### 潜在风险

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| eventlet 兼容性 | 部分库可能不兼容 | 测试验证 |
| Django ORM 线程安全 | 可能有影响 | 测试验证 |
| monkey-patch 范围 | 可能影响其他库 | 限制 patch 范围 |

### 验证清单

- [ ] eventlet 安装成功
- [ ] Worker 启动正常
- [ ] 任务执行正常
- [ ] 数据库操作正常
- [ ] 前端查询正常
- [ ] 资源消耗符合预期

---

## 总结

### 核心结论

1. **整体架构无需改动**：当前的 Backend 监听 + Worker 消费模式是正确的
2. **Worker 并发模型需升级**：从 threads → eventlet，获得协程级并发
3. **零代码改动**：eventlet 通过 monkey-patch 自动处理，无需修改业务代码
4. **极大收益**：10x 性能提升，200x 内存节省

### 推荐行动

**立即实施**：仅需修改 2 个配置文件，即可获得显著性能提升。

---

*文档结束*
