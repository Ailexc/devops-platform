# Mock 数据管理系统设计方案

> 版本：v1.0  
> 日期：2026-08-06  
> 状态：待审核

---

## 一、背景与目标

### 1.1 背景

当前系统处于 Demo 阶段，后端没有真实的 CMDB 数据。为了演示前端功能（依赖图谱、关系详情等），在前端硬编码了 Mock 数据。

**当前问题：**

| 问题 | 影响 |
|------|------|
| 前端 Mock 数据分散 | 维护困难，修改需重新构建 |
| 数据与真实结构脱节 | 前端展示与后端模型不一致 |
| 无法支持复杂查询 | 前端无法做筛选、统计等 |
| 不便于数据管理 | 无法版本控制、批量操作 |

### 1.2 目标

建立一个**后端 Mock 数据管理系统**，实现：

1. **数据集中管理**：所有 Mock 数据存储在 SQLite 数据库
2. **与真实数据共存**：通过配置开关切换 Mock/真实数据
3. **支持前端需求**：提供完整的 API 接口
4. **便于维护**：脚本化数据填充，支持版本控制

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  TopologyCompose │  │ RelationDetail  │  │  List.vue   │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
└───────────┼────────────────────┼───────────────────┼────────┘
            │                    │                   │
            ▼                    ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (Django)                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    API Views                             ││
│  │  graph_views.py / views.py / serializers.py            ││
│  └────────────────────────┬────────────────────────────────┘│
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────────┐│
│  │                   Service Layer                         ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌────────────┐  ││
│  │  │ MockService │ OR │ RealService │ OR │ HybridSvc  │  ││
│  │  └──────┬──────┘    └──────┬──────┘    └─────┬──────┘  ││
│  └─────────┼──────────────────┼──────────────────┼─────────┘│
│            │                  │                  │           │
│  ┌─────────▼──────────┐  ┌───▼──────────────────▼─────────┐│
│  │   mock.db (SQLite) │  │      MySQL (真实数据)           ││
│  └────────────────────┘  └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
backend/
├── mock_data/                          # Mock 数据目录
│   ├── __init__.py
│   ├── mock.db                         # SQLite 数据库
│   ├── schema.sql                      # 表结构定义
│   ├── seed.py                         # 数据填充脚本
│   ├── service.py                      # MockService 服务层
│   └── dumps/                          # 数据导出（可选）
│       ├── departments.json
│       ├── applications.json
│       ├── services.json
│       └── relations.json
├── cmdb/
│   ├── models.py                       # 真实数据模型
│   ├── graph.py                        # 图谱查询
│   ├── graph_views.py                  # 图谱 API
│   └── mock_views.py                   # Mock API（可选）
├── config/
│   └── settings.py                     # 配置（USE_MOCK_DATA）
└── seed_data.py                        # 旧种子脚本（保留）
```

---

## 三、数据模型设计

### 3.1 SQLite 表结构

#### 3.1.1 部门表

```sql
CREATE TABLE mock_department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES mock_department(id)
);
```

#### 3.1.2 应用表

```sql
CREATE TABLE mock_application (
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
```

#### 3.1.3 环境表

```sql
CREATE TABLE mock_environment (
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
```

#### 3.1.4 服务表

```sql
CREATE TABLE mock_service (
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
```

#### 3.1.5 服务端点表

```sql
CREATE TABLE mock_service_endpoint (
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
```

#### 3.1.6 服务依赖关系表（核心）

```sql
CREATE TABLE mock_service_relation (
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
```

#### 3.1.7 资源表（简化版）

```sql
CREATE TABLE mock_resource (
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
```

#### 3.1.8 资源关系表

```sql
CREATE TABLE mock_resource_relation (
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
```

#### 3.1.9 部署单元表

```sql
CREATE TABLE mock_deployment_unit (
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
```

#### 3.1.10 变更记录表

```sql
CREATE TABLE mock_change_record (
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
```

### 3.2 表关系图

```
mock_department ─┬─ mock_application ─┬─ mock_environment ─┬─ mock_service ─┬─ mock_service_endpoint
                 │                    │                    │                │
                 │                    │                    │                └─ mock_service_relation
                 │                    │                    │                     (source_service_id → mock_service)
                 │                    │                    │                     (target_service_id → mock_service)
                 │                    │                    │
                 │                    │                    ├─ mock_resource ─┬─ mock_resource_relation
                 │                    │                    │                 │
                 │                    │                    └─ mock_deployment_unit
                 │                    │
                 │                    └─ mock_change_record
                 │
                 └─ (支持多级部门)
```

---

## 四、API 设计

### 4.1 Mock 数据 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/mock/departments/` | 获取部门列表 |
| GET | `/api/mock/applications/` | 获取应用列表 |
| GET | `/api/mock/applications/{id}/` | 获取应用详情 |
| GET | `/api/mock/environments/` | 获取环境列表 |
| GET | `/api/mock/environments/{id}/` | 获取环境详情 |
| GET | `/api/mock/services/` | 获取服务列表 |
| GET | `/api/mock/services/{id}/` | 获取服务详情 |
| GET | `/api/mock/services/{id}/dependencies/` | 获取服务依赖 |
| GET | `/api/mock/relations/` | 获取所有关系 |
| GET | `/api/mock/relations/{id}/` | 获取关系详情 |
| POST | `/api/mock/relations/` | 创建关系 |
| PUT | `/api/mock/relations/{id}/` | 更新关系 |
| DELETE | `/api/mock/relations/{id}/` | 删除关系 |
| GET | `/api/mock/graph/environment/{id}/` | 获取环境图谱 |
| GET | `/api/mock/graph/application/{id}/` | 获取应用图谱 |
| GET | `/api/mock/deployment-units/` | 获取部署单元 |
| GET | `/api/mock/change-records/` | 获取变更记录 |

### 4.2 响应格式

#### 图谱数据

```json
{
  "nodes": [
    {
      "id": "svc:1",
      "name": "订单服务",
      "category": "service",
      "meta": {
        "service_type": "backend",
        "deploy_type": "k8s",
        "status": "running",
        "port": 8080,
        "instance_count": 3
      }
    },
    {
      "id": "res:101",
      "name": "RDS MySQL",
      "category": "resource",
      "meta": {
        "resource_type": "database",
        "status": "available",
        "region": "cn-hangzhou",
        "spec": "db.r6g.2xlarge"
      }
    }
  ],
  "edges": [
    {
      "id": 1,
      "source": "svc:1",
      "target": "svc:2",
      "relation_type": "depends_on",
      "strength": "hard",
      "metadata": {
        "protocol": "HTTP",
        "port": 8080,
        "source_domain": "order.internal",
        "target_domain": "user.internal",
        "load_balance": "round_robin",
        "timeout_ms": 3000,
        "retry_count": 3,
        "auth_type": "mTLS",
        "tracing_enabled": true,
        "critical_level": "core"
      }
    }
  ]
}
```

#### 关系详情

```json
{
  "id": 1,
  "source_service": {
    "id": 1,
    "name": "订单服务",
    "domain": "order.internal",
    "port": 8080
  },
  "target_service": {
    "id": 2,
    "name": "用户服务",
    "domain": "user.internal",
    "port": 8081
  },
  "relation_type": "depends_on",
  "strength": "hard",
  "protocol": "HTTP",
  "load_balance": "round_robin",
  "timeout_ms": 3000,
  "retry_count": 3,
  "retry_interval_ms": 100,
  "auth_type": "mTLS",
  "rate_limit": 1000,
  "tracing_enabled": true,
  "metrics_enabled": true,
  "critical_level": "core",
  "sla_target": "99.9%",
  "status": "active",
  "created_at": "2026-08-06T10:00:00Z",
  "updated_at": "2026-08-06T10:00:00Z"
}
```

---

## 五、服务层设计

### 5.1 MockService 类

```python
# mock_data/service.py

import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ServiceRelation:
    id: int
    source_service_id: int
    target_service_id: int
    relation_type: str
    strength: str
    protocol: str
    port: int
    source_domain: str
    target_domain: str
    load_balance: str
    timeout_ms: int
    retry_count: int
    auth_type: str
    rate_limit: int
    tracing_enabled: bool
    critical_level: str
    sla_target: str

class MockService:
    """Mock 数据服务层"""
    
    def __init__(self, db_path: str = 'mock_data/mock.db'):
        self.db_path = db_path
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def get_environment_graph(self, env_id: int) -> Dict:
        """获取环境的完整图谱数据"""
        nodes = self._get_nodes(env_id)
        edges = self._get_edges(env_id)
        return {'nodes': nodes, 'edges': edges}
    
    def get_service_dependencies(self, service_id: int) -> List[Dict]:
        """获取服务的所有依赖关系"""
        query = '''
            SELECT r.*, 
                   ss.name as source_name, ss.domain as source_domain,
                   ts.name as target_name, ts.domain as target_domain
            FROM mock_service_relation r
            JOIN mock_service ss ON r.source_service_id = ss.id
            JOIN mock_service ts ON r.target_service_id = ts.id
            WHERE r.source_service_id = ? OR r.target_service_id = ?
        '''
        return self.conn.execute(query, (service_id, service_id)).fetchall()
    
    def get_relation_detail(self, relation_id: int) -> Optional[Dict]:
        """获取关系详情"""
        query = '''
            SELECT r.*, 
                   ss.name as source_name, ss.domain as source_domain, ss.port as source_port,
                   ts.name as target_name, ts.domain as target_domain, ts.port as target_port
            FROM mock_service_relation r
            JOIN mock_service ss ON r.source_service_id = ss.id
            JOIN mock_service ts ON r.target_service_id = ts.id
            WHERE r.id = ?
        '''
        return self.conn.execute(query, (relation_id,)).fetchone()
    
    def create_relation(self, data: Dict) -> int:
        """创建新的依赖关系"""
        query = '''
            INSERT INTO mock_service_relation 
            (source_service_id, target_service_id, relation_type, strength, protocol, port, ...)
            VALUES (?, ?, ?, ?, ?, ?, ...)
        '''
        cursor = self.conn.execute(query, (...))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_relation(self, relation_id: int, data: Dict) -> bool:
        """更新依赖关系"""
        # 实现更新逻辑
        pass
    
    def delete_relation(self, relation_id: int) -> bool:
        """删除依赖关系"""
        # 实现删除逻辑
        pass
    
    def _get_nodes(self, env_id: int) -> List[Dict]:
        """获取环境的所有节点"""
        # 查询服务、资源等节点
        pass
    
    def _get_edges(self, env_id: int) -> List[Dict]:
        """获取环境的所有边"""
        # 查询服务间依赖、资源关系等
        pass
```

### 5.2 配置切换

```python
# config/settings.py

USE_MOCK_DATA = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'

# cmdb/service_factory.py

from django.conf import settings

def get_cmdb_service():
    if settings.USE_MOCK_DATA:
        from mock_data.service import MockService
        return MockService()
    else:
        from cmdb.real_service import RealService
        return RealService()
```

---

## 六、Mock 数据内容

### 6.1 组织架构

```
技术部
├── 交易平台
│   ├── 订单中心（3个环境）
│   │   ├── 生产环境
│   │   │   ├── 订单服务（backend）
│   │   │   ├── 用户服务（backend）
│   │   │   └── 支付服务（backend）
│   │   ├── 测试环境
│   │   └── 开发环境
│   └── 支付中心（2个环境）
│       ├── 生产环境
│       │   ├── 支付网关（gateway）
│       │   └── 账务服务（backend）
│       └── 测试环境
├── 数据平台
│   └── 数据仓库（2个环境）
└── 基础设施
    ├── 监控系统
    └── 日志平台

运维部
└── SRE团队
    └── 运维工具
```

### 6.2 服务依赖示例

```
订单服务 (backend)
├── depends_on → 用户服务 (HTTP, 8081)
├── depends_on → 支付服务 (gRPC, 9090)
├── depends_on → Redis (TCP, 6379)
└── depends_on → MySQL (TCP, 3306)

用户服务 (backend)
├── depends_on → Redis (TCP, 6379)
└── depends_on → MySQL (TCP, 3306)

支付网关 (gateway)
├── depends_on → 账务服务 (HTTP, 8082)
└── depends_on → 支付渠道 (HTTPS, 443)
```

### 6.3 关系详情示例

| 源服务 | 目标服务 | 协议 | 端口 | 超时 | 重试 | 认证 | 等级 |
|--------|----------|------|------|------|------|------|------|
| 订单服务 | 用户服务 | HTTP | 8081 | 3000ms | 3次 | mTLS | 核心 |
| 订单服务 | Redis | TCP | 6379 | 1000ms | 1次 | 密码 | 重要 |
| 支付网关 | 账务服务 | HTTP | 8082 | 5000ms | 2次 | JWT | 核心 |

---

## 七、实施步骤

### Phase 1: 基础设施（1天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1.1 | 创建 mock_data 目录结构 | 目录、__init__.py |
| 1.2 | 编写 schema.sql 表结构 | schema.sql |
| 1.3 | 初始化 SQLite 数据库 | mock.db |
| 1.4 | 实现 MockService 基础框架 | service.py |

### Phase 2: 数据填充（1.5天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 2.1 | 编写部门数据 seed | 5个部门 |
| 2.2 | 编写应用数据 seed | 5个应用 |
| 2.3 | 编写环境数据 seed | 10个环境 |
| 2.4 | 编写服务数据 seed | 20个服务 |
| 2.5 | 编写服务依赖 seed | 30条依赖关系 |
| 2.6 | 编写资源数据 seed | 50个资源 |
| 2.7 | 编写部署单元 seed | 15个部署单元 |

### Phase 3: API 实现（1.5天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 3.1 | 实现图谱查询 API | /mock/graph/ |
| 3.2 | 实现服务依赖 API | /mock/services/{id}/dependencies/ |
| 3.3 | 实现关系详情 API | /mock/relations/{id}/ |
| 3.4 | 实现关系 CRUD API | POST/PUT/DELETE |
| 3.5 | 实现部署单元 API | /mock/deployment-units/ |
| 3.6 | 实现变更记录 API | /mock/change-records/ |

### Phase 4: 前端对接（1天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 4.1 | 修改 API 配置指向 Mock API | api/index.ts |
| 4.2 | 移除前端 Mock 数据 | TopologyCompose.vue |
| 4.3 | 移除前端 Mock 数据 | RelationDetailDrawer.vue |
| 4.4 | 移除前端 Mock 数据 | List.vue |
| 4.5 | 测试完整流程 | - |

### Phase 5: 优化完善（1天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 5.1 | 添加数据导出/导入功能 | dumps/ |
| 5.3 | 编写使用文档 | README.md |
| 5.4 | 性能优化（索引、缓存） | - |

---

## 八、工作量估算

| Phase | 内容 | 工作量 | 优先级 |
|-------|------|--------|--------|
| Phase 1 | 基础设施 | 1天 | P0 |
| Phase 2 | 数据填充 | 1.5天 | P0 |
| Phase 3 | API 实现 | 1.5天 | P0 |
| Phase 4 | 前端对接 | 1天 | P1 |
| Phase 5 | 优化完善 | 1天 | P2 |
| **总计** | | **6天** | |

---

## 九、配置与切换

### 9.1 环境变量

```bash
# .env
USE_MOCK_DATA=true
MOCK_DB_PATH=mock_data/mock.db
```

### 9.2 切换方式

```python
# 开发环境：使用 Mock 数据
USE_MOCK_DATA=true

# 测试环境：使用 Mock 数据
USE_MOCK_DATA=true

# 生产环境：使用真实数据
USE_MOCK_DATA=false
```

---

## 十、风险与注意事项

### 10.1 风险

| 风险 | 影响 | 应对 |
|------|------|------|
| Mock 数据与真实数据不一致 | 前端展示异常 | 定期同步数据结构 |
| SQLite 并发性能 | 多用户同时访问 | 只读场景足够 |
| 数据量过大 | 查询变慢 | 控制数据规模 |

### 10.2 注意事项

1. **数据一致性**：Mock 数据结构需与真实模型保持同步
2. **API 兼容**：Mock API 响应格式需与真实 API 一致
3. **版本控制**：seed.py 和 schema.sql 需纳入 Git 管理
4. **测试覆盖**：Mock 数据需覆盖主要业务场景

---

## 十一、验收标准

### 11.1 功能验收

- [ ] 依赖图谱正确显示所有服务和依赖关系
- [ ] 点击连线显示完整的关系详情
- [ ] 关系详情包含协议、端口、超时、重试等信息
- [ ] 区域筛选功能正常
- [ ] 上下游视图切换正常
- [ ] 编辑模式下可添加/删除依赖
- [ ] 变更草稿功能正常

### 11.2 数据验收

- [ ] 至少 3 个部门
- [ ] 至少 5 个应用
- [ ] 至少 10 个环境
- [ ] 至少 20 个服务
- [ ] 至少 30 条服务依赖关系
- [ ] 每条依赖关系包含完整的详情字段

### 11.3 性能验收

- [ ] 图谱查询响应时间 < 500ms
- [ ] 关系详情查询响应时间 < 200ms
- [ ] 支持 10+ 并发用户

---

## 十二、附录

### 12.1 相关文件

- `backend/seed_data.py` - 旧种子脚本（参考）
- `backend/cmdb/models.py` - 真实数据模型
- `backend/cmdb/graph.py` - 图谱查询逻辑
- `frontend/src/components/topo/RelationDetailDrawer.vue` - 前端 Mock 数据

### 12.2 参考资料

- [Django SQLite 集成](https://docs.djangoproject.com/en/4.2/ref/databases/#sqlite)
- [SQLite 数据库设计最佳实践](https://www.sqlite.org/quiz.html)
- [CMDB 数据模型设计](https://en.wikipedia.org/wiki/Configuration_management_database)

---

**审核人**: _____________  
**审核日期**: _____________  
**审核意见**: _____________
