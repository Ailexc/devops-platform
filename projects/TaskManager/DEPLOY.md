# CMDB 数据维护平台 — 部署手册

> 本文档讲解如何用 **Docker** 和 **Kubernetes** 两种方式部署和管理本系统。
> 如果你对容器化不熟悉，建议**先理解概念，再动手操作**。

---

## 目录

1. [核心概念](#1-核心概念)
2. [方式一：Docker Compose（开发/测试用）](#2-方式一docker-compose开发测试用)
3. [方式二：Kubernetes（生产用）](#3-方式二kubernetes生产用)
4. [日常运维](#4-日常运维)
5. [常见问题](#5-常见问题)

---

## 1. 核心概念

### 1.1 这套系统由哪些服务组成？

我们的 CMDB 平台拆成了 **6 个服务**，每个服务运行在独立的容器中：

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
│  │              Django Backend (REST API)             │     │
│  │  大盘API · 任务API · 配置API · 历史API              │     │
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

| 服务名 | 通俗理解 | 用的什么技术 |
|--------|---------|-------------|
| **frontend** | 网页前端，用户看到的界面 | Vue.js + Nginx |
| **backend** | 后端 API，处理所有业务逻辑 | Django + DRF |
| **celery-worker** | 干苦力活的——执行同步任务 | Python Celery |
| **celery-beat** | 闹钟——定时触发同步任务 | Python Celery |
| **redis** | 临时仓库——缓存数据 + 任务队列 | Redis |
| **postgres** | 永久仓库——存业务数据 | PostgreSQL |

### 1.2 什么是 Docker？

Docker 是容器技术，可以理解为一个 **轻量级的虚拟机**。

```
┌──────────────────────────────────┐
│  你的 Mac 电脑                    │
│  ┌─────────┐  ┌──────────────┐   │
│  │ 容器 A   │  │  容器 B      │   │
│  │ (backend)│  │  (postgres)  │   │
│  │ 代码+环境 │  │  代码+环境    │   │
│  └─────────┘  └──────────────┘   │
│  ┌──────────────────────────────┐ │
│  │     Docker 引擎 (管理容器)     │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │     macOS 操作系统             │ │
│  └──────────────────────────────┘ │
└──────────────────────────────────┘
```

**关键概念：**
- **镜像 (Image)** —— 一个"安装包"，包含了运行某个软件所需的一切（代码、依赖、系统库）
- **容器 (Container)** —— 镜像"运行起来"后的实例
- **Dockerfile** —— 制作镜像的"配方/菜谱"
- **docker-compose.yml** —— 同时启动多个容器的"编排文件"

> **类比：** 镜像 = 程序安装包 (.exe)，容器 = 双击运行后的程序窗口

### 1.3 什么是 Kubernetes (K8s)？

K8s 是一个 **容器编排平台**，可以理解为"生产环境中的容器管家"。

```
┌──────────────────────────────────────────────────┐
│  K8s 集群                                          │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ 工作节点1  │  │ 工作节点2 │  │ 工作节点3 │          │
│  │ ┌──┐ ┌──┐│  │ ┌──┐ ┌──┐│  │ ┌──┐ ┌──┐│          │
│  │ │P1│ │P2││  │ │P3│ │P4││  │ │P5│ │P6││          │
│  │ └──┘ └──┘│  │ └──┘ └──┘│  │ └──┘ └──┘│          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                                                    │
│  Docker 只是单机工具，K8s 管理一群机器               │
└──────────────────────────────────────────────────┘
```

**Docker 与 K8s 的关系：**
- Docker = 一个容器引擎
- K8s = 一群机器的编排系统（内部也依赖 Docker 来运行容器）

---

## 2. 方式一：Docker Compose（开发/测试用）

### 2.1 你需要先安装什么

```bash
# 1. 安装 Docker Desktop（Mac 上最简单的方案）
#    下载地址：https://www.docker.com/products/docker-desktop/
#    安装后打开，等待 Docker 图标在顶部菜单栏稳定

# 2. 验证安装
docker --version          # 应输出 Docker 版本号
docker compose version    # 应输出 Compose 版本号
```

### 2.2 各文件的作用

#### `docker-compose.yml` — 总编排文件

这个文件定义了整个系统有哪些服务、它们之间如何连接。

```yaml
# 拆开来看每一段：

services:
  redis:              # ← 服务名
    image: redis:7-alpine          # 使用现成的官方镜像（不用自己写 Dockerfile）
    ports: ["6379:6379"]           # 端口映射：宿主机6379 → 容器6379
    volumes: ["redis_data:/data"]  # 持久化：容器内/data挂载到命名卷
    healthcheck: ...               # 健康检查：Docker 定期检查 Redis 是否活着

  backend:            # ← 后端
    build: ./backend               # 使用 Dockerfile 构建镜像（路径指向 backend/Dockerfile）
    command: sh -c "migrate && runserver"  # 容器启动后执行的命令
    ports: ["8000:8000"]
    environment:                   # 环境变量（= 代码里的 os.environ.get()）
      DEBUG: "1"
      DATABASE_URL: "postgres://cmdb:cmdb_dev@db:5432/cmdb"
    depends_on:                    # 依赖关系：先启动 redis+db，再启动 backend
      redis: { condition: service_healthy }
      db: { condition: service_healthy }

  celery_worker:     # ← 任务执行器
    build: ./backend               # 和 backend 使用同一个镜像
    command: celery -A config worker ...  # 但执行不同的命令
    # 没有 ports，因为 Worker 不需要对外暴露端口——它只管消费队列

  frontend:          # ← 前端
    build: ./frontend              # 使用 frontend/Dockerfile
    ports: ["3000:80"]             # 宿主机3000端口 → 容器80端口
```

#### `backend/Dockerfile` — 后端镜像制作"配方"

```dockerfile
# 第1步：选一个基础镜像（包含 Python 3.11 的最小 Linux 系统）
FROM python:3.11-slim

# 第2步：设置容器内的工作目录
WORKDIR /app

# 第3步：先复制依赖文件，安装 Python 包
# （先复制 requirements.txt 是为了利用 Docker 的缓存机制）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 第4步：复制所有代码到镜像
COPY . .

# 第5步：声明容器运行时监听的端口
EXPOSE 8000

# 第6步：容器启动后默认执行的命令
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

> **为什么要分层？** 因为 Docker 构建时会**缓存每一层**。如果你只改了代码，`requirements.txt` 没变，Docker 会重用第3步的缓存，只重新执行第4步，构建速度极快。

#### `frontend/Dockerfile` — 前端镜像制作"配方"

```dockerfile
# ── 第一阶段：编译 ──
FROM node:20-alpine AS builder  # 用 Node.js 镜像来构建
WORKDIR /app
COPY package.json ./
RUN npm install                  # 安装前端依赖
COPY . .
RUN npm run build                # 编译 Vue.js → 生成静态文件 dist/

# ── 第二阶段：运行 ──
FROM nginx:alpine               # 用 Nginx 镜像来托管页面
COPY --from=builder /app/dist /usr/share/nginx/html  # 从第一阶段复制编译结果
COPY nginx.conf /etc/nginx/conf.d/default.conf       # 使用自定义 Nginx 配置
EXPOSE 80
```

> **为什么要分两个阶段？** 因为 Node.js 运行时很大（几百 MB），但运行页面只需要 Nginx（几十 MB）。第一阶段用 Node 编译，第二阶段只把编译结果复制到 Nginx，最终镜像体积更小。

#### `frontend/nginx.conf` — Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # API 请求 → 转发到后端
    location /api/ {
        proxy_pass http://backend:8000;    # backend 是 docker-compose 中的服务名
        proxy_set_header Host $host;
    }

    # 前端页面 → 直接返回文件
    location / {
        try_files $uri $uri/ /index.html;  # Vue SPA 需要这个：所有路径都返回 index.html
    }
}
```

> **关键理解：** 在 Docker 网络中，容器之间通过**服务名**互相访问（`backend:8000`），而不是通过 `localhost`。每个容器都有自己的 IP，Docker 内置 DNS 会把服务名解析为 IP。

### 2.3 操作步骤

```bash
# 1. 进入项目目录
cd task-management

# 2. 启动所有服务（第一次运行需要下载镜像，较慢）
docker compose up -d
#    -d 表示后台运行（不加 -d 会在前台输出日志）

# 3. 查看服务状态
docker compose ps
# 应该看到 6 个服务都在 "Up" 状态

# 4. 查看日志
docker compose logs -f backend    # 只看 backend 的日志
docker compose logs -f            # 看所有服务的日志

# 5. 访问系统
#    前端: http://localhost:3000
#    API:  http://localhost:8000/api/v1/dashboard/stats

# 6. 如果修改了代码，需要重新构建镜像并启动
docker compose up -d --build

# 7. 停止所有服务（不会删除数据）
docker compose stop

# 8. 停止并删除容器（也不会删除数据）
docker compose down

# 9. 停止并删除容器和数据卷（⚠️ 会清空数据库！）
docker compose down -v
```

### 2.4 Docker Compose 常用命令速查

| 命令 | 作用 | 说明 |
|------|------|------|
| `docker compose up -d` | 启动所有服务 | -d 后台运行 |
| `docker compose down` | 停止并删除容器 | 数据仍在 |
| `docker compose ps` | 查看状态 | 看哪些在运行 |
| `docker compose logs -f` | 实时查看日志 | 按 Ctrl+C 退出 |
| `docker compose exec backend bash` | 进入容器内部 | 像 SSH 一样 |
| `docker compose restart backend` | 重启单个服务 | |
| `docker compose pull` | 拉取最新镜像 | 当依赖的镜像更新时 |

---

## 3. 方式二：Kubernetes（生产用）

### 3.1 K8s 资源对象对应关系

Docker Compose 中的每个概念，在 K8s 中对应更细粒度的资源对象：

```
Docker Compose              Kubernetes
──────────────────────────────────────────────────
docker-compose.yml          k8s/ 目录下的所有 .yaml 文件
service (一个服务)            Deployment + Service
container                   Pod (一个或多个容器)
端口映射 (ports)             Service (端口暴露)
环境变量                     ConfigMap + Secret
数据卷 (volumes)             PersistentVolumeClaim
健康检查                     readinessProbe + livenessProbe
```

### 3.2 各 K8s 文件的作用

#### 基础设施层（00~03）

| 文件 | 资源类型 | 作用 |
|------|---------|------|
| `00-namespace.yaml` | **Namespace** | 资源隔离空间。所有 CMDB 相关资源放在 `cmdb` 命名空间下，不会和其他服务冲突 |
| `01-configmap.yaml` | **ConfigMap** | 存放非敏感配置（如 Redis 地址、Nginx 配置）。可以理解为一个"配置文件中心" |
| `02-secret.yaml` | **Secret** | 存放敏感信息（数据库密码、Django Secret Key）。数据用 base64 编码存储 |
| `03-pvc.yaml` | **PVC** | 持久化存储声明。向 K8s 集群申请一块硬盘空间给 Redis 和 PostgreSQL 使用 |

#### 业务服务层（10~15）

| 文件 | 对应的服务 | 关键配置 |
|------|-----------|---------|
| `10-redis.yaml` | Redis | Deployment(1副本) + Service |
| `11-postgres.yaml` | PostgreSQL | **StatefulSet**(有状态应用) + Service。用 StatefulSet 而不是 Deployment，因为数据库有状态（数据不能乱丢）|
| `12-backend.yaml` | Django API | Deployment(2副本) + Service。有 **readinessProbe**（就绪检查）和 **livenessProbe**（存活检查）|
| `13-celery-worker.yaml` | Celery Worker | Deployment(2副本)。无 Service（不需要对外暴露端口）|
| `14-celery-beast.yaml` | Celery Beat | Deployment(1副本)。只能一个副本，否则会重复调度 |
| `15-frontend.yaml` | Nginx | Deployment(2副本) + Service。挂载了 ConfigMap 中的 nginx.conf |

**三种工作负载的区别：**

| 类型 | 用途 | 特点 |
|------|------|------|
| **Deployment** | 无状态应用（backend, frontend, worker） | 可以随意扩缩容，重启后不丢失数据 |
| **StatefulSet** | 有状态应用（postgres） | 每个 Pod 有固定的名称和存储，重启后数据不丢 |
| **Job** | 一次性任务 | 执行完成后 Pod 自动退出 |

#### 网络层（20）

| 文件 | 资源类型 | 作用 |
|------|---------|------|
| `20-ingress.yaml` | **Ingress** | 外部访问入口。将域名 `cmdb.example.com` 的请求路由到前端服务 |

#### 弹性伸缩层（30）

| 文件 | 资源类型 | 作用 |
|------|---------|------|
| `30-hpa.yaml` | **HPA** | HorizontalPodAutoscaler。当 CPU 使用率超过 70% 时，自动增加 Pod 副本数 |

### 3.3 K8s 核心概念详解

#### Pod

Pod 是 K8s 中最小的部署单元，可以包含一个或多个容器。

```
┌─────────────────────┐
│  Pod                 │
│  ┌─────────────────┐│
│  │ 容器 (Django)    ││
│  │ IP: 10.1.2.3    ││
│  └─────────────────┘│
│  共享网络 + 存储     │
└─────────────────────┘
```

> Pod 随时可能被 K8s 杀死、重启、迁移到其他节点——所以**不要使用 Pod 的 IP 直接访问**，要用 Service。

#### Service

Service 为 Pod 提供一个**固定的访问入口**，不管 Pod 怎么变化。

```
  ┌──────────┐
  │  Service  │  "backend-service"
  │  10.0.0.5 │  ← 这个 IP 固定不变
  └────┬─────┘
       │ 负载均衡
  ┌────┼────┐
  ▼    ▼    ▼
┌───┐ ┌───┐ ┌───┐
│P1 │ │P2 │ │P3 │  ← Pod 的 IP 可变
└───┘ └───┘ └───┘
```

#### ConfigMap 和 Secret

```
ConfigMap:                         Secret:
┌─────────────────────────┐       ┌─────────────────────────┐
│ DEBUG: "0"              │       │ DATABASE_URL: "base64.."│  ← 存储时 base64 编码
│ REDIS_URL: "redis://..."│       │ POSTGRES_PASSWORD: "..."│
│ nginx.conf: "server..." │       └─────────────────────────┘
└─────────────────────────┘       使用时 K8s 自动解码后注入
       │                                  │
       ▼                                  ▼
  Pod 启动时，K8s 将 ConfigMap/Secret 注入为环境变量或挂载为文件
```

#### 健康检查

```
readinessProbe（就绪检查）          livenessProbe（存活检查）
     │                                  │
     ▼                                  ▼
"Pod 是否准备好接收流量？"         "Pod 是否还活着？"
如果失败 → 从 Service 中移除      如果失败 → K8s 重启 Pod
```

#### HPA（自动扩缩容）

```
CPU > 70% ──────────→ 自动增加 Pod 副本数
CPU < 40% ──────────→ 自动减少 Pod 副本数
          ↓
始终保持在 minReplicas ~ maxReplicas 之间
```

### 3.4 操作步骤

#### 准备工作

```bash
# 1. 确保 K8s 集群在运行
kubectl cluster-info

# 2. 构建 Docker 镜像并推送到镜像仓库
#    （K8s 需要从镜像仓库拉取镜像，不像 docker-compose 那样直接使用本地镜像）

# 先登录镜像仓库（以 Docker Hub 为例）
docker login

# 构建后端镜像
cd backend
docker build -t your-docker-id/cmdb-backend:latest .
docker push your-docker-id/cmdb-backend:latest

# 构建前端镜像
cd ../frontend
docker build -t your-docker-id/cmdb-frontend:latest .
docker push your-docker-id/cmdb-frontend:latest
```

#### 修改镜像地址

打开 `12-backend.yaml`、`13-celery-worker.yaml`、`14-celery-beat.yaml`、`15-frontend.yaml`，将 `image:` 后面的值改为你刚才推送的镜像地址：

```yaml
# 改之前
image: cmdb-backend:latest

# 改之后
image: your-docker-id/cmdb-backend:latest
```

#### 部署到 K8s

```bash
# 方法一：使用 Kustomize（推荐，一键部署全部）
cd task-management
kubectl apply -k k8s/

# 方法二：逐个文件部署
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
# ...依次类推

# 查看部署进度
kubectl -n cmdb get pods -w    # -w 实时观察变化

# 查看所有资源
kubectl -n cmdb get all

# 查看日志
kubectl -n cmdb logs -f deployment/backend
kubectl -n cmdb logs -f deployment/celery-worker

# 进入 Pod 内部调试
kubectl -n cmdb exec -it deployment/backend -- bash
```

#### 更新代码后重新部署

```bash
# 1. 重新构建镜像
cd backend && docker build -t your-docker-id/cmdb-backend:latest . && docker push your-docker-id/cmdb-backend:latest

# 2. 滚动更新 K8s 中的 Deployment
kubectl -n cmdb rollout restart deployment/backend
kubectl -n cmdb rollout restart deployment/celery-worker
kubectl -n cmdb rollout restart deployment/celery-beat

# 3. 查看更新状态
kubectl -n cmdb rollout status deployment/backend
```

### 3.5 K8s 常用命令速查

```bash
# ── 查看资源 ──
kubectl -n cmdb get pods                    # 查看所有 Pod
kubectl -n cmdb get pods -o wide            # 查看 Pod 详细信息（IP、所在节点）
kubectl -n cmdb get deployments             # 查看所有 Deployment
kubectl -n cmdb get services                # 查看所有 Service
kubectl -n cmdb get hpa                     # 查看自动扩缩容状态

# ── 调试 ──
kubectl -n cmdb describe pod backend-xxx    # 查看 Pod 详细信息（事件、错误原因）
kubectl -n cmdb logs -f backend-xxx          # 实时查看日志
kubectl -n cmdb exec -it backend-xxx -- bash # 进入 Pod 内部

# ── 操作 ──
kubectl -n cmdb scale deployment backend --replicas=3    # 手动扩缩容
kubectl -n cmdb rollout restart deployment backend        # 滚动重启
kubectl -n cmdb rollout undo deployment backend           # 回滚到上一个版本

# ── 删除 ──
kubectl delete -k k8s/           # 删除所有通过 Kustomize 部署的资源
```

---

## 4. 日常运维

### 4.1 如何查看服务是否健康

```bash
# Docker Compose
docker compose ps                    # 查看所有容器状态
docker compose logs --tail=50 -f     # 查看最近 50 行日志

# Kubernetes
kubectl -n cmdb get pods             # 看 Pod 是否都在 Running
kubectl -n cmdb describe pod xxx     # 如果 Pod 没启动，看 Events 部分
```

### 4.2 服务不启动了怎么办？

**用 kubectl describe 查看失败原因**，这是最常用的调试命令：

```bash
kubectl -n cmdb describe pod backend-7d8f9c6b4-abc12
```

输出中的 **Events** 部分会告诉你为什么 Pod 启动失败：

```
Events:
  Type     Reason     Age   From               Message
  ----     ------     ----  ----               -------
  Warning  BackOff    2m    kubelet            Back-off restarting failed container
  Warning  Failed     1m    kubelet            Error: ImagePullBackOff  ← 镜像拉取失败
  Normal   Pulling    30s   kubelet            Pulling image "xxx"     ← 正在拉取镜像
```

**常见失败原因：**

| 现象 | 原因 | 解决 |
|------|------|------|
| `ImagePullBackOff` | 镜像地址不对或没权限 | 检查 `image:` 配置，确认已推送到仓库 |
| `CrashLoopBackOff` | 容器启动后立即崩溃 | `kubectl logs pod-name` 查看错误日志 |
| `Pending` | 资源不足 | `kubectl describe pod` 看 Events 中的资源错误 |
| `Init:Error` | 初始化容器失败 | 通常是数据库迁移失败，检查数据库连接 |

### 4.3 如何备份和恢复数据库

```bash
# Docker Compose
docker compose exec db pg_dump -U cmdb cmdb > backup_$(date +%Y%m%d).sql
docker compose exec -T db psql -U cmdb < backup.sql

# Kubernetes
kubectl -n cmdb exec deployment/postgres -- pg_dump -U cmdb cmdb > backup.sql
kubectl -n cmdb exec -i deployment/postgres -- psql -U cmdb < backup.sql
```

### 4.4 如何更新配置

```bash
# 修改 ConfigMap 后，需要重启 Deployment 才能生效
kubectl -n cmdb apply -f k8s/01-configmap.yaml
kubectl -n cmdb rollout restart deployment backend
kubectl -n cmdb rollout restart deployment celery-worker
kubectl -n cmdb rollout restart deployment frontend
```

---

## 5. 常见问题

### Q: Docker Compose 和 Kubernetes 选哪个？

| 场景 | 建议 |
|------|------|
| 本地开发、调试 | **Docker Compose** — 简单快速，一条命令启动 |
| 生产环境、需要高可用 | **Kubernetes** — 自动扩缩容、自愈、滚动更新 |
| 就一台服务器，跑个演示 | **Docker Compose** — 够用，管理成本低 |
| 团队协作，多台服务器 | **Kubernetes** — 标准化部署，方便运维 |

### Q: 第一次运行很慢怎么办？

第一次运行需要拉取镜像（从 Docker Hub 下载），取决于网速。后续运行会使用缓存，速度很快。

### Q: 如何修改数据库密码？

1. 修改 `02-secret.yaml` 中的 `POSTGRES_PASSWORD`（用 base64 编码）
2. 修改 `DATABASE_URL` 中的密码部分
3. 重新部署：`kubectl apply -f k8s/02-secret.yaml`

```bash
# 生成 base64 编码
echo -n "my_new_password" | base64
```

### Q: 数据会丢失吗？

- **Docker Compose**：容器删除后数据仍在命名卷中。只有 `docker compose down -v` 才会删除数据
- **Kubernetes**：PVC 中的数据在 Pod 删除后仍然保留。只有删除 PVC 才会删除数据

### Q: 如何让其他人访问我的服务？

- **Docker Compose**：本机访问 `localhost:3000`，局域网访问 `http://你的IP:3000`
- **Kubernetes + Ingress**：配置域名解析到集群入口，通过域名访问
