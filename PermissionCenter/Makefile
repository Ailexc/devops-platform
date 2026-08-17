.PHONY: up down seed seed-reset reset-all backup restore backend-image frontend-image run run-cmdb run-id run-agent demo web test build tidy clean logs ps

# ---- OrbStack 全栈部署（统一管理）----
backend-image:  # 宿主机交叉编译 4 个 Linux/arm64 二进制 + 构建 iam-backend 镜像
	# macOS 编译产物为 Mach-O，Linux 容器需 ELF → 交叉编译（OrbStack 容器架构 aarch64）
	cd backend && mkdir -p bin && \
	  GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bin/iam-server ./cmd/iam-server && \
	  GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bin/mock-cmdb ./cmd/mock-cmdb && \
	  GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bin/mock-identity ./cmd/mock-identity && \
	  GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bin/iam-agent ./cmd/iam-agent
	docker build -f backend/Dockerfile -t iam-backend backend

frontend-image:  # 宿主机构建 dist + 构建 iam-frontend 镜像（容器内 npm install 网络不稳定，故本地构建）
	cd frontend && npm ci && npm run build
	docker build -f frontend/Dockerfile -t iam-frontend frontend

up:          # 构建镜像并启动全栈（基础设施 + iam-server/mock-cmdb/mock-identity/iam-agent/frontend）
	$(MAKE) backend-image
	$(MAKE) frontend-image
	docker compose -f deploy/docker-compose.yml up -d --build

down:        # 停止全部（OrbStack 中同一项目统一管理）
	docker compose -f deploy/docker-compose.yml down

seed:        # 容器内写入种子数据（Go 程序，零 SQL）
	docker compose -f deploy/docker-compose.yml run --rm iam-server iam-server seed

seed-reset:  # 一键重置初始化：清空 demo 数据后按最新 seed 重建（幂等，可重复执行）
	docker compose -f deploy/docker-compose.yml run --rm iam-server iam-server seed --reset

reset-all:   # 从零到可用一键重建：构建前后端 → 启动 → 重置 seed → demo.sh 全链路验证
	$(MAKE) backend-image
	$(MAKE) frontend-image
	docker compose -f deploy/docker-compose.yml up -d --build
	$(MAKE) seed-reset
	bash scripts/demo.sh

backup:      # 备份 IAM 数据库 → backups/iam-<时间戳>.sql（--clean 便于直接恢复）
	mkdir -p backups
	docker exec iam-postgres pg_dump -U iam -d iam --clean --if-exists > backups/iam-$$(date +%Y%m%d-%H%M%S).sql
	@echo "已备份: $$(ls -t backups/iam-*.sql | head -1)"

restore:     # 从备份恢复（默认取最新）：make restore [FILE=backups/xxx.sql]
	@mkdir -p backups
	@if [ -z "$(FILE)" ]; then \
	  FILE=$$(ls -t backups/iam-*.sql 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$FILE" ]; then echo "没有可用备份，先执行 make backup"; exit 1; fi; \
	echo "恢复 $$FILE ..."; \
	docker exec -i iam-postgres psql -U iam -d iam < $$FILE && \
	docker compose -f deploy/docker-compose.yml restart iam-server

logs:        # 查看全部服务日志
	docker compose -f deploy/docker-compose.yml logs -f

ps:          # 查看全部服务状态
	docker compose -f deploy/docker-compose.yml ps

# ---- 本地开发模式（需 make up 已启动基础设施；与容器服务端口冲突时先 stop 对应服务）----
run:         # 本地启动 iam-server
	cd backend && go run ./cmd/iam-server

run-cmdb:    # 本地启动 mock-cmdb
	cd backend && go run ./cmd/mock-cmdb

run-id:      # 本地启动 mock-identity
	cd backend && go run ./cmd/mock-identity

run-agent:   # 本地启动 PDP agent
	cd backend && go run ./cmd/iam-agent

web:         # 本地启动前端管理台（需先 npm install）
	cd frontend && npm run dev

demo:        # 一键演示（正常链路→无权限→CMDB宕机降级→策略发布生效→网关）
	bash scripts/demo.sh

test:
	cd backend && go test ./...

build:
	cd backend && go build ./...

tidy:
	cd backend && go mod tidy

clean:
	rm -rf backend/bin frontend/dist
