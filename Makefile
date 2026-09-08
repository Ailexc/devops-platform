# ============================================================
# DevOpsPlatform —— 统一管理入口
# 日常：make（交互菜单）· make start · make reset · make env
# 环境：make use E=local|server|cloud（显式声明，禁止靠猜）
# 完整命令：make help
# ============================================================
SHELL := /bin/bash
.DEFAULT_GOAL := menu

DC         := docker compose
INFRA_CMP  := infra/docker-compose.yml
AUTH_DIR   := Authentication

.PHONY: help menu env use ports start down reset seed demo-reset status logs portal backup gateway-up gateway-down gateway-ps ldap build up deploy deploy-server deploy-cloud

help: ## 显示分组帮助
	@awk 'BEGIN{FS=":.*?## "} /^# @group/{gsub(/^# @group[ ]*/,""); printf "\n\033[1m%s\033[0m\n",$$0} /^[a-zA-Z_%-]+:.*?## /{printf "  \033[36m%-13s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)
	@echo ""

# @group 常用
menu: ## 交互式菜单（裸 make 进入；CI 自动降级为 help）
	@bash scripts/menu.sh

env: ## 查看当前环境与关键地址
	@bash scripts/env.sh

use: ## 切换环境（make use E=local|server|cloud）
	@bash scripts/env.sh use "$(E)"

start: ## 启动全部（缺省）/ 单项目（P=auth|cloud|...）；含演示数据确保（preflight）
	@RESET_ON_START="$(RESET_ON_START)" bash scripts/start.sh "$(P)"

down: ## 停止全部（缺省）/ 单项目（P=xx）；保留数据卷
	@bash scripts/compose.sh down "$(P)"

reset: ## 恢复出厂态（默认快速复用镜像；FULL=1 先重建镜像；P=单项目）
	@NO_BUILD=$$( [ "$(FULL)" = "1" ] && echo 0 || echo 1 ); bash scripts/reset-all.sh "$(P)"

seed: ## 补齐演示数据（幂等，不破坏现有数据）
	@bash scripts/preflight.sh

status: ## 状态总览（基础设施 + 业务容器）
	@echo "── 统一基础设施 ──"
	@$(DC) -f $(INFRA_CMP) ps
	@echo ""
	@echo "── 业务容器 ──"
	@docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'NAMES|devops|auth|cloud|event|iam|release|cmdb|task|workflow' || echo "（暂无业务容器）"

ports: ## 端口映射与网关路由清单（--doc 查看设计基准）
	@bash scripts/ports.sh

logs: ## 单项目日志（P=auth）
	@bash scripts/compose.sh logs "$(P)"

portal: ## 门户地址
	@bash scripts/env.sh portal

# @group 高级
build: ## 构建镜像（P=单项目；缺省全部）
	@bash scripts/compose.sh build "$(P)"

up: ## 裸 compose up（跳过 infra 检查/演示数据确保；日常请用 start）
	@bash scripts/compose.sh up "$(P)"

demo-reset: ## （兼容别名）= make reset
	@NO_BUILD=$$( [ "$(FULL)" = "1" ] && echo 0 || echo 1 ); bash scripts/reset-all.sh "$(P)"

backup: ## 统一数据备份（切换 backups/<时间戳>/）
	@bash scripts/backup.sh

gateway-up: ## 启动统一网关（Traefik，入口 :8088）
	@bash scripts/generate-routes.sh
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml up -d
	@bash scripts/env.sh portal

gateway-down: ## 停止统一网关
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml down

gateway-ps: ## 统一网关状态
	@$(DC) -f infra/gateway/docker-compose.yml -f infra/gateway/docker-compose.override.yml ps

ldap: ## 启动 LDAP 身份源（openldap + LAM 管理台 :8083）
	@cd $(AUTH_DIR) && $(DC) --profile ldap up -d

deploy: ## 一键部署（RESET=1 出厂态；PULL=1 拉代码；环境按 make use 声明）
	@a=""; [ "$(RESET)" = "1" ] && a="$$a --reset"; [ "$(PULL)" = "1" ] && a="$$a --pull"; bash scripts/deploy.sh $$a

deploy-server: ## （兼容别名）= 自建服务器一键部署
	@bash scripts/deploy-server.sh $(RESET)

deploy-cloud: ## （兼容别名）= 阿里云 ECS 一键部署
	@bash scripts/deploy-cloud.sh $(RESET)
