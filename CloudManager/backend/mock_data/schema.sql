-- Mock 数据库表结构
-- 用于 Demo 阶段的 CMDB 数据模拟

-- 部门表
CREATE TABLE IF NOT EXISTS mock_department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES mock_department(id)
);

-- 应用表
CREATE TABLE IF NOT EXISTS mock_application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    app_code VARCHAR(50),
    department_id INTEGER,
    owner VARCHAR(50),
    language VARCHAR(32),
    framework VARCHAR(64),
    app_type VARCHAR(32),  -- microservice/monolith/serverless
    importance_level VARCHAR(8),  -- P0/P1/P2
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES mock_department(id)
);

-- 环境表
CREATE TABLE IF NOT EXISTS mock_environment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,  -- dev/test/staging/prod
    env_type VARCHAR(16),  -- dev/test/staging/prod
    account_name VARCHAR(100),
    region VARCHAR(50),
    description TEXT,
    services_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES mock_application(id)
);

-- 服务表
CREATE TABLE IF NOT EXISTS mock_service (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    service_type VARCHAR(32),  -- frontend/backend/worker/gateway
    deploy_type VARCHAR(32),  -- vm/k8s/ecs
    status VARCHAR(16) DEFAULT 'running',
    port INTEGER,
    protocol VARCHAR(16) DEFAULT 'HTTP',
    version VARCHAR(32),
    instance_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (environment_id) REFERENCES mock_environment(id)
);

-- 服务端点表
CREATE TABLE IF NOT EXISTS mock_service_endpoint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL,
    name VARCHAR(100),
    protocol VARCHAR(16) DEFAULT 'HTTP',
    domain VARCHAR(255),
    port INTEGER,
    path VARCHAR(255),
    is_external BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES mock_service(id)
);

-- 服务依赖关系表（核心）
CREATE TABLE IF NOT EXISTS mock_service_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_service_id INTEGER NOT NULL,
    target_service_id INTEGER NOT NULL,
    relation_type VARCHAR(32) DEFAULT 'depends_on',
    strength VARCHAR(8) DEFAULT 'hard',  -- hard/soft
    
    -- 协议与端口
    protocol VARCHAR(16) DEFAULT 'HTTP',
    port INTEGER,
    
    -- 域名信息
    source_domain VARCHAR(255),
    source_port INTEGER,
    target_domain VARCHAR(255),
    target_port INTEGER,
    
    -- 流量配置
    load_balance VARCHAR(32) DEFAULT 'round_robin',  -- round_robin/weighted/random/least_conn
    timeout_ms INTEGER DEFAULT 3000,
    retry_count INTEGER DEFAULT 3,
    retry_interval_ms INTEGER DEFAULT 100,
    
    -- 安全配置
    auth_type VARCHAR(32) DEFAULT 'none',  -- none/mtls/jwt/api_key
    rate_limit INTEGER,  -- QPS
    
    -- 可观测性
    tracing_enabled BOOLEAN DEFAULT 1,
    metrics_enabled BOOLEAN DEFAULT 1,
    
    -- 依赖等级
    critical_level VARCHAR(16) DEFAULT 'important',  -- core/important/general
    sla_target VARCHAR(16),  -- 99.9%/99.95%/99.99%
    
    -- 状态
    status VARCHAR(16) DEFAULT 'active',  -- active/pending/removed
    pending_ticket_no VARCHAR(50),
    
    -- 审计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    
    FOREIGN KEY (source_service_id) REFERENCES mock_service(id),
    FOREIGN KEY (target_service_id) REFERENCES mock_service(id),
    UNIQUE(source_service_id, target_service_id, relation_type)
);

-- 资源表（简化版）
CREATE TABLE IF NOT EXISTS mock_resource (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER,
    name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(32),  -- instance/database/cache/gateway/cluster
    status VARCHAR(16) DEFAULT 'available',
    region VARCHAR(50),
    spec VARCHAR(100),
    provider VARCHAR(32),  -- aws/tencent/mock
    cloud_id VARCHAR(100),
    managed_by VARCHAR(16) DEFAULT 'cloud',  -- cloud/self
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (environment_id) REFERENCES mock_environment(id)
);

-- 资源关系表
CREATE TABLE IF NOT EXISTS mock_resource_relation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_resource_id INTEGER NOT NULL,
    target_resource_id INTEGER NOT NULL,
    relation_type VARCHAR(32),
    strength VARCHAR(8) DEFAULT 'hard',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_resource_id) REFERENCES mock_resource(id),
    FOREIGN KEY (target_resource_id) REFERENCES mock_resource(id)
);

-- 部署单元表
CREATE TABLE IF NOT EXISTS mock_deployment_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    unit_type VARCHAR(16),  -- vm/k8s/ecs
    spec VARCHAR(100),
    instance_count INTEGER DEFAULT 1,
    cpu_usage REAL,
    memory_usage REAL,
    status VARCHAR(16) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (environment_id) REFERENCES mock_environment(id)
);

-- 变更记录表
CREATE TABLE IF NOT EXISTS mock_change_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no VARCHAR(50),
    title VARCHAR(200),
    change_type VARCHAR(32),  -- relation_add/relation_remove/resource_create/...
    source_id INTEGER,
    target_id INTEGER,
    source_type VARCHAR(32),  -- service/resource
    target_type VARCHAR(32),
    old_value JSON,
    new_value JSON,
    status VARCHAR(16),  -- pending/approved/rejected/executed
    operator VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_mock_department_parent ON mock_department(parent_id);
CREATE INDEX IF NOT EXISTS idx_mock_application_department ON mock_application(department_id);
CREATE INDEX IF NOT EXISTS idx_mock_environment_application ON mock_environment(application_id);
CREATE INDEX IF NOT EXISTS idx_mock_service_environment ON mock_service(environment_id);
CREATE INDEX IF NOT EXISTS idx_mock_service_endpoint_service ON mock_service_endpoint(service_id);
CREATE INDEX IF NOT EXISTS idx_mock_service_relation_source ON mock_service_relation(source_service_id);
CREATE INDEX IF NOT EXISTS idx_mock_service_relation_target ON mock_service_relation(target_service_id);
CREATE INDEX IF NOT EXISTS idx_mock_resource_environment ON mock_resource(environment_id);
CREATE INDEX IF NOT EXISTS idx_mock_resource_relation_source ON mock_resource_relation(source_resource_id);
CREATE INDEX IF NOT EXISTS idx_mock_resource_relation_target ON mock_resource_relation(target_resource_id);
CREATE INDEX IF NOT EXISTS idx_mock_deployment_unit_environment ON mock_deployment_unit(environment_id);
CREATE INDEX IF NOT EXISTS idx_mock_change_record_ticket ON mock_change_record(ticket_no);