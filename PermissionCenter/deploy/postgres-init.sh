#!/bin/bash
# PostgreSQL 容器启动时自动创建 openfga 数据库（POSTGRES_DB 只创建 iam）
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE openfga;
EOSQL
