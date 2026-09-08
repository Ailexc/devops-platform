.PHONY: up down build logs ps restart stop hosts dev-backend dev-frontend dev-worker migrate shell lint test clean
.PHONY: up-go down-go logs-go go-dev-api go-dev-worker go-seed go-build
.PHONY: init-all init-all-local init-all-docker init-python init-go seed-all

# ═══════════════════════════════════════════════════════
# Docker 部署（推荐）
# ═══════════════════════════════════════════════════════

domains:     ## 显示 OrbStack 域名
	@echo "✅ 域名（OrbStack 自动 DNS）:"
	@echo "   http://frontend.event-management.orb.local → 前端"
	@echo "   http://api.event-management.orb.local      → Python API"
	@echo "   http://api.go-event-management.orb.local   → Go API"

up:          ## 启动全部服务（-d 后台运行）
	docker compose up -d

down:        ## 停止并移除所有容器
	docker compose down

build:       ## 重新构建镜像
	docker compose build

logs:        ## 查看日志（-f 持续追踪）
	docker compose logs -f

ps:          ## 查看服务状态
	docker compose ps

restart:     ## 重启全部服务
	docker compose restart

stop:        ## 停止全部服务（不移除容器）
	docker compose stop

# 单独控制
up-api:      ## 只启动 Python API
	docker compose up -d api

up-worker:   ## 只启动 Python Worker
	docker compose up -d worker

up-frontend: ## 只启动前端
	docker compose up -d frontend

up-infra:    ## 只启动基础设施
	docker compose up -d postgres redis rabbitmq

# ═══════════════════════════════════════════════════════
# 本地开发模式（无 Docker）
# ═══════════════════════════════════════════════════════

dev-backend:  ## 启动 Django 开发服务器
	cd backend && ../.venv/bin/python manage.py runserver 0.0.0.0:8000

dev-worker:  ## 启动 Celery Worker
	cd backend && ../.venv/bin/celery -A config worker -P threads --concurrency=10 -l info

dev-frontend: ## 启动前端开发服务器
	cd frontend && npx vite --port 3000

migrate:     ## 执行数据库迁移
	cd backend && ../.venv/bin/python manage.py makemigrations && ../.venv/bin/python manage.py migrate

shell:       ## Django shell
	cd backend && ../.venv/bin/python manage.py shell

# ═══════════════════════════════════════════════════════
# 代码质量
# ═══════════════════════════════════════════════════════

lint:        ## 代码检查
	cd backend && ../.venv/bin/ruff check .

format:      ## 代码格式化
	cd backend && ../.venv/bin/ruff format .

test:        ## 运行测试
	cd backend && ../.venv/bin/python -m pytest

test-cov:    ## 测试覆盖率
	cd backend && ../.venv/bin/python -m pytest --cov=. --cov-report=term --cov-report=html

# ═══════════════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════════════

setup:       ## 初始化本地开发环境
	cd backend && pip install -r requirements.txt
	$(MAKE) migrate
	cd frontend && npm install
	@echo "✅ Setup complete!"

clean:       ## 清理缓存文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.coverage backend/htmlcov

# ═══════════════════════════════════════════════════════
# 一键初始化（推荐）
# ═══════════════════════════════════════════════════════

init-all:     ## 一键初始化 Python + Go（自动检测环境）
	chmod +x scripts/init-all.sh && ./scripts/init-all.sh

init-all-local:  ## 一键初始化（本地模式，无 Docker）
	chmod +x scripts/init-all.sh && ./scripts/init-all.sh -m local

init-all-docker: ## 一键初始化（Docker 模式）
	chmod +x scripts/init-all.sh && ./scripts/init-all.sh -m docker

init-python:  ## 只初始化 Python 栈
	chmod +x scripts/init-all.sh && ./scripts/init-all.sh -s python

init-go:      ## 只初始化 Go 栈
	chmod +x scripts/init-all.sh && ./scripts/init-all.sh -s go

seed-all:     ## 初始化两个栈（各1000条数据，Docker模式）
	docker compose up -d postgres redis rabbitmq
	$(MAKE) migrate
	cd backend && ../.venv/bin/python manage.py seed_data --total 1000
	$(MAKE) go-seed

# ═══════════════════════════════════════════════════════
# Go 后端
# ═══════════════════════════════════════════════════════

up-go:         ## 启动 Go 后端服务
	docker compose up -d go-api go-worker

down-go:       ## 停止 Go 后端服务
	docker compose stop go-api go-worker

logs-go:       ## 查看 Go 栈日志（-f 持续追踪）
	docker compose logs -f go-api go-worker

go-dev-api:    ## 本地启动 Go API 服务
	cd backend-go && go run ./cmd/api

go-dev-worker: ## 本地启动 Go Worker
	cd backend-go && go run ./cmd/worker

go-seed:       ## 灌入/重灌 Go 栈演示数据（幂等种子随 go-api 启动执行；加 SEED_FORCE=true 强制重灌）
	SEED_FORCE=true docker compose up -d --force-recreate go-api
	$(MAKE) up-go

go-build:      ## 构建 Go 二进制文件
	cd backend-go && go build -o bin/api ./cmd/api && go build -o bin/worker ./cmd/worker

# ═══════════════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════════════

help:        ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
