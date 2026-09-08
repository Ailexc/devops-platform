#!/usr/bin/env bash
# ============================================================
# deploy-cloud —— 阿里云 ECS 一键部署（薄壳，兼容旧入口）
# 核心实现：scripts/deploy.sh（--pull 拉取 Gitee 代码 + --env cloud）
# 用法：bash scripts/deploy-cloud.sh [--reset]
# 前置条件（ECS）：SSH+Gitee 密钥、Docker+Compose、安全组放行 8088
# ============================================================
exec bash "$(dirname "$0")/deploy.sh" --pull --env cloud "$@"
