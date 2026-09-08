# Mock 数据管理系统

## 概述

Mock 数据管理系统是为 Demo 阶段设计的 CMDB 数据模拟系统。它提供了完整的模拟数据，包括部门、应用、环境、服务、依赖关系等，用于前端功能的演示和测试。

## 目录结构

```
backend/mock_data/
├── __init__.py              # 模块初始化
├── mock.db                  # SQLite 数据库（已初始化）
├── schema.sql               # 表结构定义
├── seed.py                  # 数据填充脚本
├── service.py               # MockService 服务层
├── mock_views.py            # Mock 数据 API 视图
├── mock_urls.py             # Mock 数据 URL 配置
├── init_mock.py             # 初始化脚本
└── README.md                # 本文档
```

## 快速开始

### 1. 初始化数据（Docker 部署时自动执行）

```bash
cd backend
python3 -m mock_data.init_mock
```

### 2. 访问 API

- API 根目录：`http://cloud-manager-backend.orb.local/api/mock/`
- 统计信息：`http://cloud-manager-backend.orb.local/api/mock/statistics/`

## API 文档

### 部门 API

- `GET /api/mock/departments/` - 获取部门列表
- `GET /api/mock/departments/tree/` - 获取部门树结构

### 应用 API

- `GET /api/mock/applications/` - 获取应用列表
  - 参数：`department_id` (可选) - 按部门筛选
- `GET /api/mock/applications/{id}/` - 获取应用详情

### 环境 API

- `GET /api/mock/environments/` - 获取环境列表
  - 参数：`application_id` (可选) - 按应用筛选
- `GET /api/mock/environments/{id}/` - 获取环境详情

### 服务 API

- `GET /api/mock/services/` - 获取服务列表
  - 参数：`environment_id` (可选) - 按环境筛选
- `GET /api/mock/services/{id}/` - 获取服务详情
- `GET /api/mock/services/{id}/dependencies/` - 获取服务依赖关系

### 关系 API

- `GET /api/mock/relations/` - 获取所有关系
  - 参数：`environment_id` (可选) - 按环境筛选
- `GET /api/mock/relations/{id}/` - 获取关系详情
- `POST /api/mock/relations/create/` - 创建关系
- `PUT /api/mock/relations/{id}/update/` - 更新关系
- `DELETE /api/mock/relations/{id}/delete/` - 删除关系

### 图谱 API

- `GET /api/mock/graph/environment/{id}/` - 获取环境图谱
- `GET /api/mock/graph/application/{id}/` - 获取应用图谱
  - 参数：`environment_id` (可选) - 指定环境

### 资源 API

- `GET /api/mock/resources/` - 获取资源列表
  - 参数：
    - `environment_id` (可选) - 按环境筛选
    - `resource_type` (可选) - 按资源类型筛选

### 部署单元 API

- `GET /api/mock/deployment-units/` - 获取部署单元
  - 参数：`environment_id` (可选) - 按环境筛选

### 变更记录 API

- `GET /api/mock/change-records/` - 获取变更记录
  - 参数：`ticket_no` (可选) - 按工单号筛选
- `POST /api/mock/change-records/create/` - 创建变更记录

### 统计 API

- `GET /api/mock/statistics/` - 获取统计信息

### 初始化 API

- `POST /api/mock/initialize/` - 重新初始化数据

## 数据模型

### 部门表 (mock_department)
- `id`: 部门ID
- `name`: 部门名称
- `parent_id`: 父部门ID
- `sort_order`: 排序
- `created_at`: 创建时间

### 应用表 (mock_application)
- `id`: 应用ID
- `name`: 应用名称
- `app_code`: 应用编码
- `department_id`: 所属部门
- `owner`: 负责人
- `language`: 开发语言
- `framework`: 技术框架
- `app_type`: 应用类型
- `importance_level`: 重要级别
- `description`: 描述

### 环境表 (mock_environment)
- `id`: 环境ID
- `application_id`: 所属应用
- `name`: 环境名称
- `env_type`: 环境类型 (dev/test/staging/prod)
- `account_name`: 云账号
- `region`: 地域
- `description`: 描述

### 服务表 (mock_service)
- `id`: 服务ID
- `environment_id`: 所属环境
- `name`: 服务名称
- `service_type`: 服务类型 (frontend/backend/worker/gateway)
- `deploy_type`: 部署方式 (vm/k8s/ecs)
- `status`: 状态
- `port`: 端口
- `protocol`: 协议
- `version`: 版本
- `instance_count`: 实例数

### 服务端点表 (mock_service_endpoint)
- `id`: 端点ID
- `service_id`: 所属服务
- `name`: 端点名称
- `protocol`: 协议
- `domain`: 域名
- `port`: 端口
- `path`: 路径
- `is_external`: 是否外部

### 服务依赖关系表 (mock_service_relation)
- `id`: 关系ID
- `source_service_id`: 源服务ID
- `target_service_id`: 目标服务ID
- `relation_type`: 关系类型
- `strength`: 依赖强度 (hard/soft)
- `protocol`: 协议
- `port`: 端口
- `source_domain`: 源域名
- `target_domain`: 目标域名
- `load_balance`: 负载均衡策略
- `timeout_ms`: 超时时间
- `retry_count`: 重试次数
- `auth_type`: 认证类型
- `rate_limit`: 限流 (QPS)
- `tracing_enabled`: 是否启用链路追踪
- `metrics_enabled`: 是否启用监控指标
- `critical_level`: 依赖等级
- `sla_target`: SLA目标
- `status`: 状态
- `pending_ticket_no`: 待处理工单号
- `created_by`: 创建人

### 资源表 (mock_resource)
- `id`: 资源ID
- `environment_id`: 所属环境
- `name`: 资源名称
- `resource_type`: 资源类型
- `status`: 状态
- `region`: 地域
- `spec`: 规格
- `provider`: 提供商
- `cloud_id`: 云资源ID
- `managed_by`: 资源归属

### 部署单元表 (mock_deployment_unit)
- `id`: 部署单元ID
- `environment_id`: 所属环境
- `name`: 名称
- `unit_type`: 类型
- `spec`: 规格
- `instance_count`: 实例数
- `cpu_usage`: CPU使用率
- `memory_usage`: 内存使用率
- `status`: 状态

### 变更记录表 (mock_change_record)
- `id`: 记录ID
- `ticket_no`: 工单号
- `title`: 标题
- `change_type`: 变更类型
- `source_id`: 源ID
- `target_id`: 目标ID
- `source_type`: 源类型
- `target_type`: 目标类型
- `old_value`: 旧值
- `new_value`: 新值
- `status`: 状态
- `operator`: 操作人

## 配置

在 `config/settings.py` 中配置：

```python
# Mock 数据配置
USE_MOCK_DATA = os.environ.get('USE_MOCK_DATA', 'true').lower() == 'true'
MOCK_DB_PATH = os.environ.get('MOCK_DB_PATH', os.path.join(BASE_DIR, 'mock_data', 'mock.db'))
```

环境变量：
- `USE_MOCK_DATA`: 是否使用 Mock 数据（默认 true）
- `MOCK_DB_PATH`: Mock 数据库路径

## 前端集成

在前端项目中，使用 `src/api/mock_api.ts` 中的 API 方法：

```typescript
import { mockDepartmentApi, mockApplicationApi, mockGraphApi } from '@/api/mock_api'

// 获取部门列表
const departments = await mockDepartmentApi.list()

// 获取应用详情
const app = await mockApplicationApi.detail(1)

// 获取环境图谱
const graph = await mockGraphApi.environment(1)
```

## 数据统计

运行以下命令查看数据统计：

```bash
curl http://localhost:8000/api/mock/statistics/
```

示例响应：
```json
{
  "departments": 12,
  "applications": 9,
  "environments": 15,
  "services": 26,
  "relations": 13,
  "resources": 27,
  "services_by_type": {
    "backend": 12,
    "worker": 4,
    "database": 5,
    "cache": 1,
    "gateway": 2,
    "frontend": 2
  },
  "resources_by_type": {
    "instance": 20,
    "database": 6,
    "cache": 1
  }
}
```

## 故障排除

### 1. 数据库文件不存在

运行初始化脚本：
```bash
python3 -m mock_data.init_mock
```

### 2. API 返回 500 错误

检查数据库文件是否存在：
```bash
ls -la backend/mock_data/mock.db
```

### 3. 前端无法连接 API

确保后端服务已启动：
```bash
cd backend
python3 manage.py runserver
```

## 扩展开发

### 添加新的数据表

1. 在 `schema.sql` 中添加表结构
2. 在 `service.py` 中添加相应的方法
3. 在 `mock_views.py` 中添加 API 视图
4. 在 `mock_urls.py` 中添加 URL 路由
5. 运行 `python3 -m mock_data.init_mock` 重新初始化

### 自定义数据

修改 `seed.py` 文件中的数据填充逻辑，添加自定义数据。