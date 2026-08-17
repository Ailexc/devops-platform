# CMDB 数据维护平台

> 多云资产（AWS 为主）的自动化采集、关系编排、调度监控与运维大盘一体化平台。

---

## 目录

1. [项目概览](#1-项目概览)
2. [技术栈](#2-技术栈)
3. [项目结构](#3-项目结构)
4. [快速开始](#4-快速开始)
5. [数据初始化与重置](#5-数据初始化与重置)
6. [环境变量](#6-环境变量)
7. [常用命令](#7-常用命令)
8. [部署](#8-部署)

---

## 1. 项目概览

```
┌──────────────────────────────────────────────────────────┐
│                   用户访问 (浏览器)                        │
│                        │                                 │
│                        ▼                                 │
│  ┌─────────┐    ┌──────────────┐                         │
│  │ Frontend │───▶│  Nginx 反向   │  ← 前端页面 + API 代理  │
│  │ (Vue.js) │    │  代理         │                         │
│  └──────────┘    └──────┬───────┘                         │
│                         │ /api/*                          │
│                         ▼                                 │
│  ┌──────────────────────────────────────────────────┐     │
│              Django Backend (REST API)               │     │
│  │  大盘 · 任务树 · 配置管理 · 执行历史 · OpenAPI    │     │
│  └────────┬──────────────┬────────────────┬──────────┘     │
│           │              │                │                │
│           ▼              ▼                ▼                │
│  ┌────────────┐  ┌──────────────┐  ┌──────────┐           │
│  │ PostgreSQL │  │   Redis      │  │ Celery   │           │
│  │ (主数据库)  │  │ (缓存+队列)   │  │ Worker   │           │
│  └────────────┘  └──────────────┘  │ + Beat   │           │
│                                    └──────────┘           │
└──────────────────────────────────────────────────────────┘
```

**核心能力：**
- 🖥️ **监控大盘** — 任务执行趋势、健康度、资源分布、告警事件一览
- 🌲 **任务树** — 按 账号 → 区域 → 资源组 → 资源/关系 四级树形管理
- ⚙️ **配置管理** — 账号区域配置、定时策略、并发数可在线调整
- 📜 **执行历史** — 全量/增量任务的执行记录、日聚合统计、一键重试
- 🔄 **调度引擎** — Celery Beat 定时触发 + 手动触发 + 配置联动
- 🔗 **关系编排** — EC2→VPC、RDS→安全组等资源关联关系自动采集

---

## 2. 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| **前端** | Vue 3 + Vite + Vue Router | 单页应用，通过 Nginx 反代 |
| **后端 (Python)** | Django 4.2 + DRF + Celery | REST API + 异步任务 |
| **后端 (Go)** | Gin + GORM + asynq | 高性能重写版（可选） |
| **数据库** | PostgreSQL 15 | 主数据存储 |
| **缓存/队列** | Redis 7 | Celery Broker + 缓存 |
| **调度** | django-celery-beat | 动态 Cron 调度 |
| **容器** | Docker Compose / K8s | 开发/生产部署 |

---

## 3. 项目结构

```
TaskManager/
├── backend/              # Django 后端
│   ├── config/           # Django 项目配置 (settings, urls, celery)
│   ├── core/             # 核心业务（模型、服务、管理命令）
│   │   ├── management/commands/
│   │   │   ├── seed_demo_data.py   # 演示数据播种
│   │   │   └── reset_data.py       # ⭐ 完全数据重置
│   │   ├── startup.py             # 启动幂等初始化
│   │   ├── config_service.py      # 配置层服务
│   │   ├── schedule_manager.py    # 调度层管理
│   │   └── models.py              # AccountRegion 模型
│   ├── api/              # API 视图层
│   │   ├── dashboard/    # 大盘统计
│   │   ├── tasks/        # 任务树管理
│   │   ├── config/       # 配置管理
│   │   └── history/      # 执行历史
│   ├── orchestrator/     # 编排引擎（注册表 + 主编排器）
│   └── resource_modules/ # 资源模块 (EC2/EBS/ELB/IAM/RDS/VPC)
├── go-backend/           # Go 重写版（可选）
├── frontend/             # Vue.js 前端
├── k8s/                  # Kubernetes 部署清单
├── docker-compose.yml    # Docker Compose 编排
├── DEPLOY.md             # 部署手册
└── README.md             # 👈 本文件
```

---

## 4. 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 启动全部服务（首次会自动 migrate + seed）
docker compose up -d

# 2. 访问
#    前端: http://localhost (或 orb.local 域名)
#    API:  http://localhost:8000
#    文档: http://localhost:8000/docs/
```

### 方式二：本地开发

```bash
# 1. 启动依赖服务
docker compose up -d db redis

# 2. Python 环境
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. 数据库迁移 + 初始化数据
python manage.py migrate
python manage.py seed_demo_data

# 4. 启动后端
python manage.py runserver 0.0.0.0:8000

# 5. 启动 Celery Worker（新终端）
celery -A config worker -l info

# 6. 启动 Celery Beat（新终端）
celery -A config beat -l info

# 7. 启动前端（新终端）
cd frontend && npm install && npm run dev
```

---

## 5. 数据初始化与重置 ⭐

系统通过管理命令实现**一键初始化**和**完全重置**，无需手动操作数据库。

### 数据初始化流程

```
启动 / manage.py seed_demo_data
  │
  ├─ migrate          ← 建表（如尚未执行）
  ├─ AccountRegion    ← 3 个环境 × 多区域的配置数据
  ├─ PeriodicTask     ← 按 (账号,区域,资源组,任务节点) 预建调度占位
  ├─ CrontabSchedule  ← 维护任务 Cron（每日 03:30 清理）
  ├─ ExecutionRecord  ← 15 条演示执行历史
  ├─ DailyTaskStat    ← 近 7 天聚合统计
  └─ DemoStore        ← 内存演示数据（大盘/Worker/告警等）
```

### 命令一览

| 命令 | 作用 | 场景 |
|------|------|------|
| `python manage.py seed_demo_data` | 播种演示数据（幂等，已有则跳过） | 首次启动、补充数据 |
| `python manage.py seed_demo_data --reset` | 清空后重新播种 | 需要刷新演示数据 |
| `python manage.py reset_data` | **完全重置**所有业务数据并重新播种 | 脏数据/恶意删除后恢复 |
| `python manage.py reset_data --dry` | 仅查看将清空的内容，不执行 | 确认重置范围 |
| `python manage.py reset_data --no-seed` | 仅清空，不重新播种 | 准备导入自定义数据 |

### 完全重置（推荐）

当数据被注入脏数据、恶意删除、或需要恢复出厂状态时：

```bash
# 查看重置范围（安全预览）
python manage.py reset_data --dry

# 执行完全重置（清空 → 重新播种）
python manage.py reset_data

# 仅清空（不自动播种）
python manage.py reset_data --no-seed
```

**重置覆盖范围：**

| 数据类型 | 模型 | 说明 |
|----------|------|------|
| 执行历史 | `ExecutionRecord` | 全部任务执行记录 |
| 日聚合统计 | `DailyTaskStat` | 大盘趋势数据 |
| 账号区域配置 | `AccountRegion` | 3 环境 × 8 区域 |
| 周期调度任务 | `PeriodicTask` | Celery Beat 动态调度 |
| Crontab | `CrontabSchedule` | Cron 表达式定义 |
| 任务结果 | `TaskResult` | Celery 执行结果缓存 |
| 内存数据 | `DemoStore` | 大盘/Worker/告警演示数据 |

### Docker Compose 中重置

```bash
# 在运行中的容器内执行
docker compose exec backend python manage.py reset_data
```

---

## 6. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgres://cmdb:cmdb_dev@localhost:5432/cmdb` | 数据库连接 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `DEBUG` | `1` | 调试模式 |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Django 密钥 |
| `ALLOWED_HOSTS` | `*` | 允许的域名 |

---

## 7. 常用命令

```bash
# 数据管理
python manage.py seed_demo_data           # 播种演示数据
python manage.py reset_data               # 完全重置并重新播种

# 数据库
python manage.py migrate                  # 执行数据库迁移
python manage.py makemigrations           # 生成迁移文件

# Django
python manage.py createsuperuser          # 创建管理员账号
python manage.py collectstatic            # 收集静态文件

# Celery
celery -A config worker -l info           # 启动 Worker
celery -A config beat -l info             # 启动 Beat 调度器
celery -A config inspect active           # 查看活跃任务
```

---

## 8. 部署

详细部署指南请参考 [DEPLOY.md](./DEPLOY.md)，包含：

- **Docker Compose** — 开发/测试一键部署
- **Kubernetes** — 生产环境部署（含 HPA 自动扩缩容）
- **域名配置** — OrbStack 本地域名 / 生产 Ingress

---

## License

Internal use only.
