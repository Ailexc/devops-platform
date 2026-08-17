#!/bin/bash
# Create additional databases for Go backend
# PostgreSQL already creates POSTGRES_DB on first start

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE eventdb_go;
    GRANT ALL PRIVILEGES ON DATABASE eventdb_go TO $POSTGRES_USER;
EOSQL

echo "✅ Created database eventdb_go"
