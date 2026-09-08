# cloud_manager — 多云管理系统 Demo

> 基于过往真实工作经历复刻的多云管理系统 Demo，用于技术复盘巩固与面试项目展示。

## 一、项目定位

- **不是**从零研发的商用系统，而是对真实工作中参与过的多云管理系统进行**模拟复刻**与**适度扩展**
- 核心用途：① 复盘巩固技术知识点；② 作为面试项目成果演示
- 开发原则：**先还原真实架构与核心能力，再适度扩展；扩展不脱离技术现实、不过度虚构**

## 二、核心架构（真实项目骨架）

```
前端（仿 AWS 控制台） ──REST API──▶ 后端服务层 ──转发──▶ 工单系统 ──执行──▶ CMDB
   ▲                                                          │
   └──────────────── 展示数据全部从 CMDB 拉取 ◀────────────────┘
```

- **前端**：友好可视化入口，按资源模块分区（计算/网络/存储/安全组/子网），承接运维操作
- **后端**：不直接执行云操作，所有操作请求转发工单系统
- **工单系统**：流程编排、审批流转、自动化任务执行
- **CMDB**：配置管理数据库，所有资源基础数据的唯一权威源

## 三、技术栈（建议选型，最终需与真实工作经历一致）

| 层 | 建议 | 说明 |
|---|---|---|
| 后端 | Java + Spring Boot | 国内企业多云管理系统最常见选型 |
| 前端 | Vue 3 + Ant Design Vue | 易于实现仿 AWS 控制台风格 |
| 数据库 | MySQL + Redis | 业务数据 + 缓存 |
| 消息 | RabbitMQ | 异步工单 / 任务 |
| 云 SDK | AWS SDK、阿里云 SDK | 多云适配层 |
| 部署 | Docker Compose | Demo 一键启动 |

## 四、文档索引

| 文档 | 内容 |
|---|---|
| [docs/01-项目需求与背景.md](docs/01-项目需求与背景.md) | 需求说明、核心诉求与约束 |
| [docs/02-系统架构设计.md](docs/02-系统架构设计.md) | 四层架构、模块划分、云适配层、关键设计决策 |
| [docs/03-功能扩展方案.md](docs/03-功能扩展方案.md) | 扩展方向评估矩阵、分层方案、防穿帮清单 |
| [docs/04-技术选型.md](docs/04-技术选型.md) | 技术选型对比与说明 |
| [docs/05-数据库设计.md](docs/05-数据库设计.md) | CMDB / 工单 / 权限 / 成本 / 服务目录表结构 |
| [docs/06-面试准备.md](docs/06-面试准备.md) | 叙事线、深度问题与应答要点 |
| [docs/07-开发路线图.md](docs/07-开发路线图.md) | P1~P4 分阶段落地计划 |

## 五、开发路线图（概要）

| 阶段 | 内容 | 产出 |
|---|---|---|
| P1 | 架构还原：AWS 资源管理 + 工单 + CMDB 骨架 | 跑通最小闭环 |
| P2 | 多云适配层 + 阿里云 Provider + 统一资源模型 | 真正"多云" |
| P3 | 服务目录自服务 + 权限审计 + CMDB 深化 | 业务闭环完善 |
| P4 | 成本管理 + 智能资源建议 | 面试亮点冲刺 |

详细计划见 [docs/07-开发路线图.md](docs/07-开发路线图.md)。

## 六、部署方式

### Docker Compose 部署（推荐）

```bash
# 1. 构建前端
cd frontend && pnpm install && pnpm build && cd ..

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库密码等

# 3. 一键部署
docker compose -f docker-compose.yml up -d --build

# 4. 查看日志
docker compose -f docker-compose.yml logs -f

# 5. 停止服务
docker compose -f docker-compose.yml down
```

### 数据一键重置 / 初始化（本地开发）

本地开发时，用 `reset_db.sh` 一键恢复**整个项目数据**（清空 → 迁移 → 全链路种子数据 → 成本优化报告与建议）：

```bash
./reset_db.sh            # 交互确认后重置
./reset_db.sh --yes      # 跳过交互确认（CI / 无交互环境）
```

| 参数 | 说明 |
|---|---|
| `--yes` / `-y` | 跳过删除数据库前的交互确认 |
| `--no-backup` | 不备份旧库（默认自动备份到 `backend/backups/时间戳/`） |
| `--skip-report` | 不生成成本优化报告（默认会调用 `run_all` 生成） |

执行链路（8 步）：

```bash
migrate → seed_data.py → init_mock → seed_rules
       → seed_multicloud → seed_metrics → seed_knowledge → run_all(优化报告)
```

- 自动识别根目录 `.venv`，也兼容系统 `python3`
- 尊重 `DB_ENGINE` / `DB_NAME` / `MOCK_DB_PATH` 环境变量（与 `settings.py` 一致）；检测到 MySQL 引擎时不删库文件，以幂等方式灌入
- 重置后演示账号统一为 `admin / admin123` 等（见下方演示账号表）

### 服务访问

| 服务 | 地址 | 说明 |
|---|---|---|
| 前端 | http://cloud-manager-nginx.orb.local | OrbStack 自动域名 |
| 后端 API | http://cloud-manager-backend.orb.local/api/ | OrbStack 自动域名 |

### 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 超级管理员 |
| cloud_admin | admin123 | 云管理员 |
| ops_user | admin123 | 运维工程师 |
| readonly | admin123 | 只读用户 |
| Redis | localhost:6379 | 生产环境 |

### 5. 部署文档

详细部署指南见 [docs/08-部署指南.md](docs/08-部署指南.md)
