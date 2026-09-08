# 初始化脚本使用示例

## 场景1: 首次初始化（推荐）

```bash
# 自动检测环境，初始化两个栈
make init-all
```

这将：
1. 自动检测是否使用 Docker 或本地环境
2. 初始化 Python 栈（迁移 + 生成 1000 条数据）
3. 初始化 Go 栈（迁移 + 生成 1000 条数据）

## 场景2: 重置数据

```bash
# 清空现有数据，重新生成
./scripts/init-all.sh -c
```

或者指定数量：

```bash
# 生成 5000 条数据，先清空
./scripts/init-all.sh -t 5000 -c
```

## 场景3: 只初始化某个栈

```bash
# 只初始化 Python 栈
make init-python

# 只初始化 Go 栈
make init-go
```

## 场景4: 指定环境模式

```bash
# 强制使用本地模式（无 Docker）
make init-all-local

# 强制使用 Docker 模式
make init-all-docker
```

## 场景5: 开发环境快速设置

```bash
# 1. 先安装依赖
make setup

# 2. 初始化数据
make init-all

# 3. 启动开发服务器
make dev-backend  # Python 后端
make go-dev-api   # Go 后端
```

## 场景6: Docker 环境完整初始化

```bash
# 1. 启动所有服务
make up

# 2. 初始化数据
make init-all-docker

# 3. 查看服务状态
make ps
```

## 高级用法

### 自定义初始化脚本

```bash
# 查看所有参数
./scripts/init-all.sh --help

# 示例：初始化 Go 栈，生成 2000 条数据，清空现有数据
./scripts/init-all.sh -s go -t 2000 -c -m docker
```

### 在 CI/CD 中使用

```bash
# 在 Docker 环境中初始化
./scripts/init-all.sh -m docker -t 1000

# 或者只初始化特定栈
./scripts/init-all.sh -s python -m docker
```

### 批量测试

```bash
# 循环测试不同数据量
for count in 100 500 1000 5000; do
    echo "测试 $count 条数据..."
    ./scripts/init-all.sh -t $count -c
    # 运行测试...
done
```

## 故障排除

### 问题: Python 虚拟环境未激活

```bash
# 手动激活虚拟环境
source .venv/bin/activate

# 然后运行初始化
make init-all
```

### 问题: PostgreSQL 未运行

```bash
# 启动 PostgreSQL（macOS）
brew services start postgresql

# 或者使用 Docker
docker compose up -d postgres
```

### 问题: Docker 服务未启动

```bash
# 启动 Docker 服务
make up

# 等待服务就绪
sleep 10

# 然后初始化
make init-all-docker
```

## 验证初始化结果

### 检查 Python 栈

```bash
# 查看数据库表
cd backend && python manage.py shell

# 在 Django shell 中执行：
>>> from apps.event_store.models import Event
>>> print(f"Python 栈事件数量: {Event.objects.count()}")
```

### 检查 Go 栈

```bash
# 使用 psql 检查
psql -h localhost -p 5433 -U eventuser -d eventdb_go

# 在 PostgreSQL 中执行：
SELECT COUNT(*) FROM api_event;
```

### 通过 API 检查

```bash
# Python API
curl http://localhost:8000/api/v1/events/ | jq '.count'

# Go API
curl http://localhost:8001/api/v1/events/ | jq '.count'
```

## 性能参考

| 数据量 | Python 初始化时间 | Go 初始化时间 |
|--------|------------------|--------------|
| 100    | ~2 秒            | ~1 秒        |
| 1000   | ~5 秒            | ~3 秒        |
| 5000   | ~15 秒           | ~10 秒       |
| 10000  | ~30 秒           | ~20 秒       |

*注：时间取决于硬件性能和数据库状态*
