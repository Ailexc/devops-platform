# 开发规范 — OrbStack 本地开发

> 最后更新：2026-08-07

## 核心原则

**本地开发不使用 localhost/端口映射，全部通过 OrbStack 自动域名访问。**

### 为什么？

当同时开发多个项目时，端口冲突是最大的痛点：

| 项目 | 默认端口 | 冲突风险 |
|------|----------|----------|
| cloud_manager | 3000, 8000, 3306, 6379 | 🔴 与其他项目冲突 |
| permission-center | 8080, 8088, 5432 | 🔴 与其他项目冲突 |
| workflow | 80, 443, 8000, 5432, 6379 | 🔴 与其他项目冲突 |

OrbStack 为每个 docker-compose 项目自动分配 DNS 域名，完全消除端口冲突。

---

## OrbStack 域名规则

OrbStack 自动为 docker-compose 中的每个容器生成域名：

```
格式: {container_name}.orb.local
规则: 容器名中的下划线(_)自动转为连字符(-)
```

### 本项目域名

| 服务 | 容器名 | OrbStack 域名 | 用途 |
|------|--------|---------------|------|
| 前端 | cloud_manager_nginx | `http://cloud-manager-nginx.orb.local` | 访问入口 |
| 后端 | cloud_manager_backend | `http://cloud-manager-backend.orb.local` | API 服务 |
| MySQL | cloud_manager_mysql | `cloud-manager-mysql.orb.local` | 数据库（容器内使用） |
| Redis | cloud_manager_redis | `cloud-manager-redis.orb.local` | 缓存（容器内使用） |

### 开发环境访问

```
前端: http://cloud-manager-nginx.orb.local
后端: http://cloud-manager-backend.orb.local/api/
```

---

## 禁止事项

### ❌ 禁止暴露端口到宿主机

```yaml
# 错误 ❌ — 暴露端口到宿主机，会占用 3000/8000/3306 等端口
ports:
  - "3000:80"
  - "8000:8000"

# 正确 ✅ — 不暴露端口，通过 OrbStack 域名访问
# 不写 ports 字段，OrbStack 自动提供 DNS 解析
```

### ❌ 禁止代码中写死 localhost

```python
# 错误 ❌
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 正确 ✅ — 只允许容器名和 OrbStack 域名
ALLOWED_HOSTS = ['backend', 'cloud-manager-backend.orb.local', '*']
```

```yaml
# 错误 ❌
proxy: { target: 'http://localhost:8888' }

# 正确 ✅ — 使用容器名（容器间通信）
proxy: { target: 'http://backend:8000' }
```

### ❌ 禁止本地 runserver 启动后端

```bash
# 错误 ❌ — 本地直接运行 Django，与 Docker 环境不一致
python3 manage.py runserver 0.0.0.0:8000

# 正确 ✅ — 通过 Docker 部署
docker compose -f docker-compose.yml up -d --build
```

---

## 各项目端口分配（仅限需要端口映射时的备用方案）

如果某些场景确实需要端口映射（如 IDE 调试），按以下规则分配：

| 项目 | 前端 | 后端 | 数据库 | Redis |
|------|------|------|--------|-------|
| cloud_manager | 3080 | — | — | — |
| permission-center | 8088 | 8090 | 5432 | — |
| workflow | — | 8000 | 5433 | 6380 |

> **优先使用 OrbStack 域名，端口映射仅作为备用方案。**

---

## Docker Compose 配置模板

```yaml
services:
  nginx:
    container_name: myproject_nginx
    # 不写 ports — 通过 myproject-nginx.orb.local 访问
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
    networks:
      - net

  backend:
    container_name: myproject_backend
    # 不写 ports — 通过容器名 backend 通信
    networks:
      - net

networks:
  net:
    driver: bridge
```

---

## 快速检查命令

```bash
# 查看当前项目所有容器
docker compose -f docker-compose.yml ps

# 查看 OrbStack 分配的域名
docker inspect --format '{{.Name}}' $(docker ps -q) | sed 's/^[\/ ]*//' | sed 's/_/-/g' | awk '{print $0".orb.local"}'

# 验证域名可达
curl -s -o /dev/null -w "%{http_code}" http://cloud-manager-nginx.orb.local

# 查看端口占用情况
docker ps --format '{{.Names}}\t{{.Ports}}' | grep '0.0.0.0'
```

---

## FAQ

### Q: 为什么不用 localhost:端口？
A: 多个项目同时开发时，端口冲突导致频繁修改配置、互相干扰。OrbStack 域名方案彻底解决此问题。

### Q: OrbStack 域名是永久的吗？
A: 不是。容器重建后域名会重新分配，但名称不变（因为容器名固定）。

### Q: 容器间如何通信？
A: Docker 网络内使用服务名（如 `backend`）或容器名（如 `cloud_manager_backend`）。

### Q: 如何从宿主机浏览器访问？
A: 直接访问 `http://{container_name}.orb.local`，OrbStack 自动解析。
