-- 0001_create_tables.sql
-- Initial schema for CMDB Go backend

CREATE TABLE IF NOT EXISTS execution_records (
    id BIGSERIAL PRIMARY KEY,
    scope VARCHAR(20) DEFAULT 'region',
    parent_id BIGINT REFERENCES execution_records(id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    module VARCHAR(50) DEFAULT 'AWS',
    target VARCHAR(300) DEFAULT '',
    trigger VARCHAR(50) DEFAULT '',
    status VARCHAR(20) DEFAULT 'pending',
    celery_task_id VARCHAR(200) DEFAULT '' INDEX,
    error TEXT DEFAULT '',
    detail TEXT DEFAULT '',
    duration VARCHAR(30) DEFAULT '-',
    result JSONB,
    lifecycle_events JSONB DEFAULT '[]',
    params JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP
);

CREATE INDEX idx_execution_records_parent_id ON execution_records(parent_id);
CREATE INDEX idx_execution_records_status ON execution_records(status);
CREATE INDEX idx_execution_records_started_at ON execution_records(started_at);

CREATE TABLE IF NOT EXISTS daily_task_stats (
    id BIGSERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    module VARCHAR(50) DEFAULT 'AWS',
    total INTEGER DEFAULT 0,
    success INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    total_duration FLOAT DEFAULT 0,
    synced_count INTEGER DEFAULT 0,
    UNIQUE(stat_date, module)
);

CREATE INDEX idx_daily_task_stats_date ON daily_task_stats(stat_date);

CREATE TABLE IF NOT EXISTS account_regions (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(100) NOT NULL,
    account_id VARCHAR(50) DEFAULT '',
    region VARCHAR(50) NOT NULL,
    endpoint VARCHAR(300) DEFAULT '',
    cron VARCHAR(50) DEFAULT '0 2 * * *',
    concurrency INTEGER DEFAULT 50,
    source VARCHAR(20) DEFAULT 'seed',
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(account, region)
);

CREATE TABLE IF NOT EXISTS periodic_tasks (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    task VARCHAR(200) DEFAULT '',
    enabled BOOLEAN DEFAULT FALSE,
    crontab VARCHAR(100) DEFAULT '',
    args TEXT DEFAULT '',
    kwargs TEXT DEFAULT '',
    last_run_at TIMESTAMP,
    total_run_count INTEGER DEFAULT 0
);
