-- Migration 000001: Initialize schema matching Django models exactly

-- Events table
CREATE TABLE IF NOT EXISTS api_event (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(128) NOT NULL DEFAULT '',
    source          VARCHAR(64)  NOT NULL DEFAULT '',
    detail_type     VARCHAR(64)  NOT NULL DEFAULT '',
    resource_id     VARCHAR(256) NOT NULL DEFAULT '',
    raw_payload     JSONB        NOT NULL DEFAULT '{}',
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending',
    trace_id        UUID,
    retry_count     INT          NOT NULL DEFAULT 0,
    max_retries     INT          NOT NULL DEFAULT 5,
    handler         VARCHAR(128) NOT NULL DEFAULT '',
    worker_id       VARCHAR(64)  NOT NULL DEFAULT '',
    error_message   TEXT         NOT NULL DEFAULT '',
    received_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ,

    CONSTRAINT chk_event_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dlq'))
);

CREATE INDEX IF NOT EXISTS idx_event_event_type   ON api_event (event_type);
CREATE INDEX IF NOT EXISTS idx_event_source       ON api_event (source);
CREATE INDEX IF NOT EXISTS idx_event_status       ON api_event (status);
CREATE INDEX IF NOT EXISTS idx_event_trace_id     ON api_event (trace_id);

-- Event logs table
CREATE TABLE IF NOT EXISTS api_eventlog (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id    UUID        NOT NULL REFERENCES api_event(id) ON DELETE CASCADE,
    action      VARCHAR(32) NOT NULL DEFAULT '',
    detail      JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eventlog_event_id ON api_eventlog (event_id);

-- Event handler config table
CREATE TABLE IF NOT EXISTS api_eventhandlerconfig (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               VARCHAR(128) NOT NULL UNIQUE,
    event_type_pattern VARCHAR(256) NOT NULL DEFAULT '',
    handler_class      VARCHAR(256) NOT NULL DEFAULT '',
    timeout            INT          NOT NULL DEFAULT 60,
    max_retries        INT          NOT NULL DEFAULT 5,
    is_active          BOOLEAN      NOT NULL DEFAULT true,
    description        TEXT         NOT NULL DEFAULT '',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);
