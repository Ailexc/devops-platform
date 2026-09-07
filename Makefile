# ============================================================
# DevOpsPlatform —— 统一管理入口
# 目标：统一构建 / 统一部署 / 统一数据重置 / 统一入口
# 快速开始：make bootstrap → make up P=auth → make status
# 完整命令：make help
# ============================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

# ---------- 配置 ----------
DC         := docker compose
INFRA_CMP  := infra/docker-compose.yml

# 项目短名 → 目录
AUTH_DIR    := Authentication
CLOUD_DIR   := CloudManager
EVENT_DIR   := EventManager
IAM_DIR     := PermissionCenter
RELEASE_DIR := ReleaseManager
CMDB_DIR    := TaskManager
WORKFLOW_DIR:= WorkFlowCenter

PROJECT_DIRS := $(AUTH_DIR) $(CLOUD_DIR) $(EVENT_DIR) $(IAM_DIR) $(RELEASE_DIR) $(CMDB_DIR) $(WORKFLOW_DIR)

# 统一 PostgreSQL 的业务库（一实例多库）
DBS := devops_auth devops_cloud devops_event devops_iam devops_release devops_cmdb devops_workflow

.PHONY: help bootstrap status build up start down seed reset demo-reset ps logs portal backup gateway-up gateway-down gateway-ps

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

bootstrap: ## 启动统一基础设施（PostgreSQL + Redis）并创建 10 个业务库
	@bash scripts/bootstrap.sh

status: ## 查看统一基础设施与业务容器状态
	@echo "── 统一基础设施 ──"
	@$(DC) -f $(INFRA_CMP) ps
	@echo ""
	@echo "── 业务容器 ──"
	@docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'NAMES|devops|auth|cloud|event|iam|release|cmdb|task|workflow' || echo "（暂无业务容器）"

build: ## 构建镜像（make build P=auth 单项目；不带 P 则全部）
	@bash scripts/compose.sh build "$(P)"

up: ## 启动（make up P=auth 单项目；不带 P 则全部，不重置数据）
	@bash scripts/compose.sh up "$(P)"

start: ## 统一启动入口（make start P=auth；RESET_ON_START=true 先重置出厂态再启动）
	@RESET_ON_START="$(RESET_ON_START)" bash scripts/start.sh "$(P)"

down: ## 停止（make down P=auth 单项目；不带 P 则全部，保留数据卷）
	@bash scripts/compose.sh down "$(P)"

seed: ## 初始化数据（make seed P=auth 单项目；不带 P 则全部）
	@bash scripts/seed.sh "$(P)"

reset: ## 数据重置（make reset P=auth 单项目；不带 P 则全量重置回出厂态）
	@bash scripts/reset-all.sh "$(P)"

demo-reset: ## 一键恢复到干净出厂态（演示专用：DB 硬重建 + Redis 清空 + 全部重建启动 + 冒烟）
	@bash scripts/demo-reset.sh

backup: ## 统一数据备份（切换到 backups/<时间戳>/）
	@bash scripts/backup.sh

ps: status ## 同 status

logs: ## 查看单项目日志（make logs P=auth）
	@bash scripts/compose.sh logs "$(P)"

portal: ## 打开统一门户（本地 OrbStack 用 orb.local；服务器用 SERVER_IP:8088）
	@SERVER_IP=$$(grep '^SERVER_IP=' deploy/server/.env.server 2>/dev/null | cut -d= -f2); \
	if [ -n "$$SERVER_IP" ]; then \
		echo "门户地址：http://$$SERVER_IP:8088"; \
	else \
		open http://portal.authentication.orb.local 2>/dev/null || echo "门户地址：http://portal.authentication.orb.local"; \
	fi

gateway-up: ## 启动统一网关（Traefik 聚合 7 系统，入口 *.devops.orb.local）
	@bash scripts/generate-routes.sh
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml up -d
	@SERVER_IP=$$(grep '^SERVER_IP=' deploy/server/.env.server 2>/dev/null | cut -d= -f2); \
	if [ -n "$$SERVER_IP" ]; then \
		echo "统一入口：http://$$SERVER_IP:8088 （Dashboard: http://$$SERVER_IP:8086/dashboard/）"; \
	else \
		echo "统一入口：http://portal.devops.orb.local （Dashboard: http://traefik.devops.orb.local）"; \
	fi

gateway-down: ## 停止统一网关
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml down

gateway-ps: ## 查看统一网关状态与路由
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml ps

ldap: ## 启动 LDAP 身份源（openldap + LAM 管理台 :8083，--profile ldap）
	@cd $(AUTH_DIR) && $(DC) --profile ldap up -d

deploy-server: ## 一键部署到本地/自建服务器（构建 iam 镜像 + bootstrap + start + gateway + 验证）
	@bash scripts/deploy-server.sh $(RESET)
