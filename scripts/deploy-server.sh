#!/usr/bin/env bash
# ============================================================
# deploy-server —— 自建服务器一键部署（薄壳，兼容旧入口）
# 核心实现：scripts/deploy.sh（--env server；步骤含 preflight 演示数据）
# 用法：bash scripts/deploy-server.sh [--reset]
# 前置条件：Docker 已装；deploy/server/.env.server 已配置（SERVER_IP 等）
# ============================================================
exec bash "$(dirname "$0")/deploy.sh" --env server "$@"
