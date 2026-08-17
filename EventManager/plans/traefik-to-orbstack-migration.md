# 路由架构迁移方案：Traefik → OrbStack 原生路由

> 编写时间：2026-08-02
> 状态：🟢 迁移全部完成 — 三个项目已走纯 OrbStack 原生路由，Traefik 网关与 homepage 门户已下线

---

## 一、背景

### 1.1 当前架构

```
浏览器
  ↓ DNS 解析
OrbStack 虚拟网关 (192.168.138.4)
  ↓ Host 头路由（反向代理）
Traefik (192.168.97.3:80)
  ↓ Host 头二次路由
后端服务 (api / frontend / worker)
```

三层链路：**OrbStack → Traefik → 服务**

### 1.2 演变历史

| 阶段 | 方案 | 动机 |
|---|---|---|
| v1 | `/etc/hosts` + 端口号区分 | 每个项目不同端口，记忆困难 |
| v2 | Traefik + `/etc/hosts` 域名 | 用域名区分项目，不用记端口 |
| v3 | Traefik + homepage 门户 | 门户页面汇总所有服务链接，不用记域名 |
| v4 | OrbStack 切换（当前） | macOS Docker 性能问题，切换到 OrbStack |

OrbStack 自带 `*.orb.local` DNS 解析，本质上已经替代了 Traefik 的路由功能。

### 1.3 核心问题

**每次容器重建后，路由必然中断 3-5 秒。**

```
docker compose up -d (重建容器)
  → OrbStack 检测到容器变更
  → OrbStack 反向代理映射短暂失效
  → 请求被错误转发到其他容器（如 release-backend）
  → 返回 {"detail":"Not Found"} 或 400
  → 需要 docker restart traefik-gateway 临时修复
```

根因：**双层反向代理做同一件事**，OrbStack 和 Traefik 的路由映射更新不是原子的。

---

## 二、方案对比

| | 方案 A：/etc/hosts 直连 Traefik | 方案 B：纯 OrbStack（✅ 采用） | 方案 C：维持现状 |
|---|---|---|---|
| 路由层级 | OrbStack DNS → Traefik | OrbStack DNS + 反向代理 → 服务 | 同左 |
| 容器重建影响 | 需固定 IP + 改 hosts | 无影响（OrbStack 自动恢复） | 每次重启 traefik |
| 运维成本 | 手动维护 hosts | 零 | 每次部署多一步 |
| 前端 API 调用 | 跨域或反代 | nginx 反代（同源） | 跨域 |
| 适合场景 | 生产环境 | 本地开发演示 | 不推荐 |

### 选择方案 B 的理由

1. OrbStack 的 `dev.orbstack.domains` 标签天然支持 DNS + 反向代理
2. 容器重建后自动恢复映射，无需手动干预
3. 不需要额外的反向代理层（Traefik），架构更简单
4. 本地开发演示不需要 CORS、限流等中间件

---

## 三、影响面分析

### 3.1 涉及的项目和容器

| 项目 | 容器 | 当前域名 | 使用 Traefik |
|---|---|---|---|
| event-management | cmdb-event-api | `api.event-management.orb.local` | ✅ |
| event-management | cmdb-event-frontend | `frontend.event-management.orb.local` | ✅ |
| release-system | release-backend | `api.release-system.orb.local` | ✅ |
| release-system | release-frontend | `frontend.release-system.orb.local` | ✅ |
| release-system | release-executor | `executor.release-system.orb.local` | ✅ |
| task-management | cmdb-task-backend | `api.task-management.orb.local` | ✅ |
| task-management | task-management-frontend-1 | `frontend.task-management.orb.local` | ✅ |
| traefik-gateway | traefik-gateway | `traefik.traefik-gateway.orb.local` | 可停用 |
| traefik-gateway | homepage | `homepage.traefik-gateway.orb.local` | 可停用 |

### 3.2 各项目对 Traefik 的依赖

| 依赖项 | event-mgmt | release-sys | task-mgmt |
|---|---|---|---|
| Traefik labels | ✅ 有 | ✅ 有 | ✅ 有 |
| `local-net` 网络 | ✅ `proxy` | ✅ `local-net` | ✅ `proxy` |
| Traefik 中间件 | ❌ 无 | ❌ 无 | ❌ 无 |
| 前端 API 域名 | 硬编码（Dockerfile） | 相对路径 `/api/v1` | 相对路径 `/api/v1` |

**关键发现：三个项目都没有使用任何 Traefik 中间件。** Traefik 实际只做了最简单的 Host 头路由。

### 3.3 前端 API 调用方式

| 项目 | 前端 API 地址 | 改动 |
|---|---|---|
| event-management | `VITE_API_BASE_URL=http://api.../api/v1`（Dockerfile 注入） | 需改为 nginx 反代 |
| release-system | `/api/v1`（相对路径，已在用反代） | 无需改动 |
| task-management | `/api/v1`（相对路径，已在用反代） | 无需改动 |

---

## 四、改造计划

### 阶段一：event-management（当前项目）

#### 4.1 docker-compose.yml

**删除：**
- 文件头部注释中的 Traefik 相关说明
- api 服务的 `proxy` 网络引用 + 4 行 Traefik labels
- worker 服务的 `proxy` 网络引用
- frontend 服务的 `proxy` 网络引用 + 4 行 Traefik labels
- `proxy: name: local-net external: true` 网络定义
- frontend 服务的 `VITE_API_BASE_URL` 构建参数

**新增：**
- api 服务 labels: `dev.orbstack.domains=api.event-management.orb.local`
- frontend 服务 labels: `dev.orbstack.domains=frontend.event-management.orb.local`

#### 4.2 docker/nginx.conf

新增 `/api/` 反向代理：

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://cmdb-event-api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 4.3 docker/Dockerfile.frontend

- 删除 `ARG VITE_API_BASE_URL=...`
- 删除 build 命令中的环境变量传递
- 简化为 `RUN npm run build`

#### 4.4 Makefile

- 删除 `build:` 和 `restart:` 中的 `docker restart traefik-gateway`
- 将 `hosts:` target 改为 `domains:`，只显示 OrbStack 域名信息

#### 4.5 前端代码

**零改动。** `api.ts` 和 `TestLab.tsx` 中的 `import.meta.env.VITE_API_BASE_URL || '/api/v1'` 在没有注入环境变量时已 fallback 到 `/api/v1`，nginx 反代后同源访问。

---

### 阶段二：停止 Traefik

```bash
docker stop traefik-gateway homepage && docker rm traefik-gateway homepage
```

### 阶段三：release-system

#### 4.6 docker-compose.yml

**删除：**
- backend / frontend / executor 三个服务的 `local-net` 网络引用
- 三个服务各自的 Traefik labels（共 9 行）
- homepage 服务的 `local-net` 网络引用
- `local-net` 网络定义

**新增：**
- backend labels: `dev.orbstack.domains=api.release-system.orb.local`
- frontend labels: `dev.orbstack.domains=frontend.release-system.orb.local`
- executor labels: `dev.orbstack.domains=executor.release-system.orb.local`

#### 4.7 新增 docker/nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://release-backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> ⚠️ 需确认：backend 容器名、API 路径前缀

### 阶段四：task-management

#### 4.8 docker-compose.yml

**删除：**
- backend / frontend 的 `proxy` 网络引用
- 两个服务各自的 Traefik labels
- `proxy: name: local-net` 网络定义

**新增：**
- backend labels: `dev.orbstack.domains=api.task-management.orb.local`
- frontend labels: `dev.orbstack.domains=frontend.task-management.orb.local`

#### 4.9 新增 docker/nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://cmdb-task-backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> ⚠️ 需确认：backend 容器名、API 路径前缀

---

## 五、当前进度

| 阶段 | 状态 | 说明 |
|---|---|---|
| ✅ event-management docker-compose.yml | 已完成 | 删除 Traefik，添加 OrbStack 标签 |
| ✅ event-management nginx.conf | 已完成 | 添加 `/api/` 反代 |
| ✅ event-management Dockerfile.frontend | 已完成 | 移除 VITE_API_BASE_URL |
| ✅ event-management Makefile | 已完成 | 清理 Traefik 相关 |
| ✅ event-management 镜像构建 | 已完成 | `docker compose build` 成功 |
| ✅ event-management 部署验证 | 已完成 | 三端点全通 + 重建自动恢复，详见第六节 |
| ✅ release-system 迁移 | 已完成 | 三域名（frontend/api/executor）全通 + 重建自动恢复 |
| ✅ task-management 迁移 | 已完成 | frontend/api 两域名全通 + 重建自动恢复 |
| ✅ 停止 traefik-gateway | 已完成 | 与 homepage 一并下线，业务路由零影响 |

---

## 六、问题解决记录（2026-08-02）

### 6.1 前端 nginx 反代 404 —— ✅ 已解决

**真实根因（两层）：**

1. **OrbStack 域名路由冲突（主因）**
   - `traefik-gateway` 容器的 `dev.orbstack.domains` 标签仍包含 `frontend.event-management.orb.local` 和 `api.event-management.orb.local`
   - 与 `cmdb-event-frontend` / `cmdb-event-api` 的新标签**冲突**
   - OrbStack 将 event 域名流量路由到 traefik-gateway（而非新容器），Traefik 无对应 router → 404
   - 佐证：OrbStack 日志（`~/.orbstack/log/vmgr.log`）反复出现 `dns: name already in use`

2. **Django ALLOWED_HOSTS 缺失（次因，主因修复后暴露）**
   - nginx 反代时 `proxy_set_header Host $host` 把 `frontend.event-management.orb.local` 传给后端
   - Django `ALLOWED_HOSTS` 只有 `api.*`，反代返回 400
   - 修复：`ALLOWED_HOSTS` 增加 `frontend.${COMPOSE_PROJECT_NAME:-event-management}.orb.local`

**排除的误判：**
- nginx `proxy_pass` 路径拼接无问题（`/api/` + `/api/v1/` = `/api/v1/`，实测反代返回真实数据）
- 容器内 `wget localhost` 失败是 IPv6 假象（wget 解析到 `::1`，nginx 只监听 IPv4），非真实故障

**修复步骤：**
1. 编辑 `traefik_gateway/docker-compose.yml`，从 `dev.orbstack.domains` 移除 event 两个域名
2. `docker compose up -d --force-recreate traefik` 重建 Traefik（标签变更生效）
3. 重建 `cmdb-event-frontend` / `cmdb-event-api` 仍报 `name already in use` → **重启 OrbStack** 清理陈旧 DNS 注册表
4. 修复 `ALLOWED_HOSTS` 后重建 api 容器

**验证结果：**
- `frontend.event-management.orb.local/` → 200
- `frontend.event-management.orb.local/api/v1/events` → 200（反代）
- `api.event-management.orb.local/api/v1/events` → 200（直连）
- Dashboard 页面完整渲染（数据全部来自反代 API）
- 容器重建后路由自动恢复（无需任何手动干预）✅

### 6.2 旧 traefik-gateway 仍在运行 —— ✅ 已处理

- 已从 Traefik 标签移除 event 域名（release/task 域名保留，等迁移）
- 最终停止 traefik-gateway 放在全部项目迁移完成后执行

### 6.3 迁移经验（对 release-system / task-management 的指导）

- **迁移每个项目时必须同步从 Traefik 的 `dev.orbstack.domains` 标签移除其域名**，否则 OrbStack 路由冲突
- 标签冲突后 OrbStack 的 DNS 注册表可能残留陈旧记录，需要**重启 OrbStack** 清理
- nginx 反代后后端收到的 Host 是 frontend 域名，**Django ALLOWED_HOSTS 必须包含 frontend 域名**
- 迁移完成后容器重建自动恢复路由，彻底摆脱"重启 traefik 修复"

---

## 七、改造后的架构

```
改造后:
浏览器
  ↓ DNS 解析
OrbStack 虚拟网关 (192.168.138.4)
  ↓ Host 头路由（反向代理）
前端容器 (nginx)
  ├── /          → SPA 静态文件
  └── /api/      → proxy_pass → API 容器
```

**容器重建时：**
```
docker compose up -d (重建容器)
  → OrbStack 检测到容器变更
  → 自动更新 dev.orbstack.domains 映射
  → 无中断（OrbStack 原生行为）
```

---

## 八、验证清单

- [x] event-management 前端页面可正常加载（2026-08-02 验证）
- [x] event-management API 通过 `/api/v1/` 反代可访问（2026-08-02 验证）
- [x] event-management API 直连 `api.event-management.orb.local` 可访问（2026-08-02 验证）
- [x] 容器重建后路由自动恢复（无手动干预）（2026-08-02 验证）
- [x] release-system 前端/API 正常（2026-08-02 验证）
- [x] release-system executor 域名正常（2026-08-02 验证）
- [x] task-management 前端/API 正常（2026-08-02 验证）
- [x] traefik-gateway 已停止（2026-08-02 与 homepage 一并下线）
- [x] 所有项目的 Makefile / 脚本已清理（无 Traefik 残留引用）
