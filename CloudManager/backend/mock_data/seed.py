"""
Mock 数据填充脚本
用于生成 Demo 阶段的 CMDB 模拟数据
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime, timedelta
import random


class MockDataSeeder:
    """Mock 数据填充器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = Path(__file__).parent
            self.db_path = str(base_dir / 'mock.db')
        else:
            self.db_path = db_path
        
        # 清除现有数据
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def run(self):
        """执行数据填充"""
        print("开始填充 Mock 数据...")
        
        # 创建表结构
        self._create_tables()
        
        # 填充数据
        departments = self._seed_departments()
        applications = self._seed_applications(departments)
        environments = self._seed_environments(applications)
        services = self._seed_services(environments)
        self._seed_service_endpoints(services)
        self._seed_service_relations(services)
        self._seed_resources(environments)
        self._seed_deployment_units(environments)
        self._seed_change_records()
        
        print("Mock 数据填充完成！")
        print(f"数据库路径: {self.db_path}")
    
    def _create_tables(self):
        """创建表结构"""
        conn = sqlite3.connect(self.db_path)
        schema_path = Path(__file__).parent / 'schema.sql'
        
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.close()
    
    def _seed_departments(self) -> dict:
        """填充部门数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        departments = [
            (1, '技术部', None, 1),
            (2, '交易平台', 1, 2),
            (3, '订单中心', 2, 3),
            (4, '支付中心', 2, 4),
            (5, '数据平台', 1, 5),
            (6, '数据仓库', 5, 6),
            (7, '基础设施', 1, 7),
            (8, '监控系统', 7, 8),
            (9, '日志平台', 7, 9),
            (10, '运维部', None, 10),
            (11, 'SRE团队', 10, 11),
            (12, '运维工具', 11, 12),
        ]
        
        cursor.executemany(
            'INSERT INTO mock_department (id, name, parent_id, sort_order) VALUES (?, ?, ?, ?)',
            departments
        )
        
        conn.commit()
        conn.close()
        
        return {d[0]: d[1] for d in departments}
    
    def _seed_applications(self, departments: dict) -> dict:
        """填充应用数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        applications = [
            (1, '订单服务', 'ORDER_SVC', 3, '张三', 'Java', 'Spring Boot', 'microservice', 'P0', '核心订单处理服务'),
            (2, '用户服务', 'USER_SVC', 3, '李四', 'Java', 'Spring Boot', 'microservice', 'P0', '用户信息管理服务'),
            (3, '支付服务', 'PAY_SVC', 4, '王五', 'Java', 'Spring Boot', 'microservice', 'P0', '支付处理服务'),
            (4, '支付网关', 'PAY_GW', 4, '赵六', 'Go', 'Gin', 'gateway', 'P0', '支付网关服务'),
            (5, '账务服务', 'ACCT_SVC', 4, '钱七', 'Java', 'Spring Boot', 'microservice', 'P1', '账务处理服务'),
            (6, '数据仓库', 'DW_SVC', 6, '孙八', 'Python', 'Spark', 'bigdata_job', 'P1', '数据仓库服务'),
            (7, '监控系统', 'MON_SVC', 8, '周九', 'Go', 'Prometheus', 'microservice', 'P1', '监控数据采集'),
            (8, '日志平台', 'LOG_SVC', 9, '吴十', 'Java', 'ELK', 'microservice', 'P1', '日志收集分析'),
            (9, '运维工具', 'OPS_TOOL', 12, '郑十一', 'Python', 'Django', 'internal_tool', 'P2', '运维自动化工具'),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_application 
               (id, name, app_code, department_id, owner, language, framework, app_type, importance_level, description) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            applications
        )
        
        conn.commit()
        conn.close()
        
        return {a[0]: a[1] for a in applications}
    
    def _seed_environments(self, applications: dict) -> dict:
        """填充环境数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        environments = [
            # 订单服务环境
            (1, 1, '生产环境', 'prod', '云账号A', 'cn-hangzhou', '订单服务生产环境'),
            (2, 1, '测试环境', 'test', '云账号A', 'cn-hangzhou', '订单服务测试环境'),
            (3, 1, '开发环境', 'dev', '云账号A', 'cn-hangzhou', '订单服务开发环境'),
            # 用户服务环境
            (4, 2, '生产环境', 'prod', '云账号A', 'cn-hangzhou', '用户服务生产环境'),
            (5, 2, '测试环境', 'test', '云账号A', 'cn-hangzhou', '用户服务测试环境'),
            # 支付服务环境
            (6, 3, '生产环境', 'prod', '云账号B', 'cn-shanghai', '支付服务生产环境'),
            (7, 3, '测试环境', 'test', '云账号B', 'cn-shanghai', '支付服务测试环境'),
            # 支付网关环境
            (8, 4, '生产环境', 'prod', '云账号B', 'cn-shanghai', '支付网关生产环境'),
            (9, 4, '测试环境', 'test', '云账号B', 'cn-shanghai', '支付网关测试环境'),
            # 账务服务环境
            (10, 5, '生产环境', 'prod', '云账号B', 'cn-shanghai', '账务服务生产环境'),
            # 数据仓库环境
            (11, 6, '生产环境', 'prod', '云账号C', 'cn-beijing', '数据仓库生产环境'),
            (12, 6, '测试环境', 'test', '云账号C', 'cn-beijing', '数据仓库测试环境'),
            # 监控系统环境
            (13, 7, '生产环境', 'prod', '云账号A', 'cn-hangzhou', '监控系统生产环境'),
            # 日志平台环境
            (14, 8, '生产环境', 'prod', '云账号A', 'cn-hangzhou', '日志平台生产环境'),
            # 运维工具环境
            (15, 9, '生产环境', 'prod', '云账号A', 'cn-hangzhou', '运维工具生产环境'),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_environment 
               (id, application_id, name, env_type, account_name, region, description) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            environments
        )
        
        conn.commit()
        conn.close()
        
        return {e[0]: {'app_id': e[1], 'name': e[2], 'env_type': e[3]} for e in environments}
    
    def _seed_services(self, environments: dict) -> dict:
        """填充服务数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        services = [
            # 订单服务 - 生产环境
            (1, 1, '订单API', 'backend', 'k8s', 'running', 8080, 'HTTP', '1.0.0', 3),
            (2, 1, '订单Worker', 'worker', 'k8s', 'running', None, None, '1.0.0', 2),
            (3, 1, '订单数据库', 'database', 'ecs', 'running', 3306, 'TCP', '5.7', 1),
            # 订单服务 - 测试环境
            (4, 2, '订单API', 'backend', 'k8s', 'running', 8080, 'HTTP', '1.0.0', 1),
            (5, 2, '订单Worker', 'worker', 'k8s', 'running', None, None, '1.0.0', 1),
            # 用户服务 - 生产环境
            (6, 4, '用户API', 'backend', 'k8s', 'running', 8081, 'HTTP', '1.0.0', 2),
            (7, 4, '用户缓存', 'cache', 'ecs', 'running', 6379, 'TCP', '6.0', 1),
            (8, 4, '用户数据库', 'database', 'ecs', 'running', 3306, 'TCP', '5.7', 1),
            # 用户服务 - 测试环境
            (9, 5, '用户API', 'backend', 'k8s', 'running', 8081, 'HTTP', '1.0.0', 1),
            # 支付服务 - 生产环境
            (10, 6, '支付API', 'backend', 'k8s', 'running', 8082, 'HTTP', '1.0.0', 2),
            (11, 6, '支付Worker', 'worker', 'k8s', 'running', None, None, '1.0.0', 1),
            (12, 6, '支付数据库', 'database', 'ecs', 'running', 3306, 'TCP', '5.7', 1),
            # 支付服务 - 测试环境
            (13, 7, '支付API', 'backend', 'k8s', 'running', 8082, 'HTTP', '1.0.0', 1),
            # 支付网关 - 生产环境
            (14, 8, '支付网关', 'gateway', 'k8s', 'running', 443, 'HTTPS', '1.0.0', 2),
            # 支付网关 - 测试环境
            (15, 9, '支付网关', 'gateway', 'k8s', 'running', 443, 'HTTPS', '1.0.0', 1),
            # 账务服务 - 生产环境
            (16, 10, '账务API', 'backend', 'k8s', 'running', 8083, 'HTTP', '1.0.0', 2),
            (17, 10, '账务数据库', 'database', 'ecs', 'running', 3306, 'TCP', '5.7', 1),
            # 数据仓库 - 生产环境
            (18, 11, '数据采集', 'worker', 'k8s', 'running', None, None, '1.0.0', 3),
            (19, 11, '数据处理', 'worker', 'k8s', 'running', None, None, '1.0.0', 2),
            (20, 11, '数据存储', 'database', 'ecs', 'running', 9000, 'HTTP', '1.0.0', 1),
            # 监控系统 - 生产环境
            (21, 13, 'Prometheus', 'backend', 'k8s', 'running', 9090, 'HTTP', '2.45.0', 1),
            (22, 13, 'Grafana', 'frontend', 'k8s', 'running', 3000, 'HTTP', '10.0.0', 1),
            # 日志平台 - 生产环境
            (23, 14, 'Elasticsearch', 'database', 'k8s', 'running', 9200, 'HTTP', '8.10.0', 3),
            (24, 14, 'Kibana', 'frontend', 'k8s', 'running', 5601, 'HTTP', '8.10.0', 1),
            # 运维工具 - 生产环境
            (25, 15, '运维API', 'backend', 'k8s', 'running', 8090, 'HTTP', '1.0.0', 1),
            (26, 15, '任务调度', 'worker', 'k8s', 'running', None, None, '1.0.0', 1),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_service 
               (id, environment_id, name, service_type, deploy_type, status, port, protocol, version, instance_count) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            services
        )
        
        conn.commit()
        conn.close()
        
        return {s[0]: {'env_id': s[1], 'name': s[2], 'type': s[3]} for s in services}
    
    def _seed_service_endpoints(self, services: dict):
        """填充服务端点数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        endpoints = [
            # 订单API端点
            (1, 1, 'order-api-http', 'HTTP', 'order.internal', 8080, '/api/orders', 0),
            (2, 1, 'order-api-grpc', 'gRPC', 'order.internal', 9090, None, 0),
            # 用户API端点
            (3, 6, 'user-api-http', 'HTTP', 'user.internal', 8081, '/api/users', 0),
            # 支付API端点
            (4, 10, 'pay-api-http', 'HTTP', 'pay.internal', 8082, '/api/payments', 0),
            (5, 10, 'pay-api-grpc', 'gRPC', 'pay.internal', 9091, None, 0),
            # 支付网关端点
            (6, 14, 'pay-gateway-https', 'HTTPS', 'pay.example.com', 443, '/api/gateway', 1),
            # 账务API端点
            (7, 16, 'account-api-http', 'HTTP', 'account.internal', 8083, '/api/accounts', 0),
            # 监控端点
            (8, 21, 'prometheus-http', 'HTTP', 'prometheus.internal', 9090, '/api/v1', 0),
            (9, 22, 'grafana-http', 'HTTP', 'grafana.internal', 3000, '/', 0),
            # 日志端点
            (10, 23, 'elasticsearch-http', 'HTTP', 'elasticsearch.internal', 9200, '/_search', 0),
            (11, 24, 'kibana-http', 'HTTP', 'kibana.internal', 5601, '/', 0),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_service_endpoint 
               (id, service_id, name, protocol, domain, port, path, is_external) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            endpoints
        )
        
        conn.commit()
        conn.close()
    
    def _seed_service_relations(self, services: dict):
        """填充服务依赖关系数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        relations = [
            # 订单服务依赖
            (1, 1, 6, 'depends_on', 'hard', 'HTTP', 8081, 'order.internal', 8080, 'user.internal', 8081,
             'round_robin', 3000, 3, 100, 'mTLS', 1000, 1, 1, 'core', '99.9%', 'active', None, 'admin'),
            (2, 1, 10, 'depends_on', 'hard', 'gRPC', 9091, 'order.internal', 8080, 'pay.internal', 9091,
             'round_robin', 5000, 2, 200, 'mTLS', 500, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            (3, 1, 3, 'depends_on', 'hard', 'TCP', 3306, 'order.internal', 8080, 'order-db.internal', 3306,
             'round_robin', 1000, 1, 0, 'none', None, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            # 用户服务依赖
            (4, 6, 7, 'depends_on', 'hard', 'TCP', 6379, 'user.internal', 8081, 'user-cache.internal', 6379,
             'round_robin', 500, 1, 0, 'password', None, 1, 1, 'important', '99.9%', 'active', None, 'admin'),
            (5, 6, 8, 'depends_on', 'hard', 'TCP', 3306, 'user.internal', 8081, 'user-db.internal', 3306,
             'round_robin', 1000, 1, 0, 'none', None, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            # 支付服务依赖
            (6, 10, 12, 'depends_on', 'hard', 'TCP', 3306, 'pay.internal', 8082, 'pay-db.internal', 3306,
             'round_robin', 1000, 1, 0, 'none', None, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            # 支付网关依赖
            (7, 14, 10, 'depends_on', 'hard', 'HTTP', 8082, 'pay.example.com', 443, 'pay.internal', 8082,
             'round_robin', 5000, 2, 200, 'mTLS', 2000, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            (8, 14, 16, 'depends_on', 'hard', 'HTTP', 8083, 'pay.example.com', 443, 'account.internal', 8083,
             'round_robin', 5000, 2, 200, 'JWT', 1000, 1, 1, 'core', '99.9%', 'active', None, 'admin'),
            # 账务服务依赖
            (9, 16, 17, 'depends_on', 'hard', 'TCP', 3306, 'account.internal', 8083, 'account-db.internal', 3306,
             'round_robin', 1000, 1, 0, 'none', None, 1, 1, 'core', '99.99%', 'active', None, 'admin'),
            # 监控系统依赖
            (10, 22, 21, 'depends_on', 'hard', 'HTTP', 9090, 'grafana.internal', 3000, 'prometheus.internal', 9090,
             'round_robin', 3000, 3, 100, 'none', None, 1, 1, 'important', '99.9%', 'active', None, 'admin'),
            # 日志平台依赖
            (11, 24, 23, 'depends_on', 'hard', 'HTTP', 9200, 'kibana.internal', 5601, 'elasticsearch.internal', 9200,
             'round_robin', 5000, 3, 200, 'none', None, 1, 1, 'important', '99.9%', 'active', None, 'admin'),
            # 跨服务依赖（测试环境）
            (12, 4, 9, 'depends_on', 'soft', 'HTTP', 8081, 'order-test.internal', 8080, 'user-test.internal', 8081,
             'round_robin', 3000, 3, 100, 'none', None, 0, 0, 'general', None, 'active', None, 'admin'),
            (13, 4, 13, 'depends_on', 'soft', 'gRPC', 9091, 'order-test.internal', 8080, 'pay-test.internal', 9091,
             'round_robin', 5000, 2, 200, 'none', None, 0, 0, 'general', None, 'active', None, 'admin'),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_service_relation 
               (id, source_service_id, target_service_id, relation_type, strength, protocol, port,
                source_domain, source_port, target_domain, target_port,
                load_balance, timeout_ms, retry_count, retry_interval_ms,
                auth_type, rate_limit, tracing_enabled, metrics_enabled,
                critical_level, sla_target, status, pending_ticket_no, created_by) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            relations
        )
        
        conn.commit()
        conn.close()
    
    def _seed_resources(self, environments: dict):
        """填充资源数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        resources = [
            # 订单服务资源
            (1, 1, 'order-api-pod-1', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-001', 'cloud'),
            (2, 1, 'order-api-pod-2', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-002', 'cloud'),
            (3, 1, 'order-api-pod-3', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-003', 'cloud'),
            (4, 1, 'order-db-mysql', 'database', 'running', 'cn-hangzhou', 'db.r6g.2xlarge', 'mock', 'rds-001', 'cloud'),
            # 用户服务资源
            (5, 4, 'user-api-pod-1', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-011', 'cloud'),
            (6, 4, 'user-api-pod-2', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-012', 'cloud'),
            (7, 4, 'user-cache-redis', 'cache', 'running', 'cn-hangzhou', 'redis.r6g.large', 'mock', 'redis-001', 'cloud'),
            (8, 4, 'user-db-mysql', 'database', 'running', 'cn-hangzhou', 'db.r6g.xlarge', 'mock', 'rds-002', 'cloud'),
            # 支付服务资源
            (9, 6, 'pay-api-pod-1', 'instance', 'running', 'cn-shanghai', '4C8G', 'mock', 'pod-021', 'cloud'),
            (10, 6, 'pay-api-pod-2', 'instance', 'running', 'cn-shanghai', '4C8G', 'mock', 'pod-022', 'cloud'),
            (11, 6, 'pay-db-mysql', 'database', 'running', 'cn-shanghai', 'db.r6g.2xlarge', 'mock', 'rds-003', 'cloud'),
            # 支付网关资源
            (12, 8, 'pay-gw-pod-1', 'instance', 'running', 'cn-shanghai', '2C4G', 'mock', 'pod-031', 'cloud'),
            (13, 8, 'pay-gw-pod-2', 'instance', 'running', 'cn-shanghai', '2C4G', 'mock', 'pod-032', 'cloud'),
            # 账务服务资源
            (14, 10, 'account-api-pod-1', 'instance', 'running', 'cn-shanghai', '4C8G', 'mock', 'pod-041', 'cloud'),
            (15, 10, 'account-api-pod-2', 'instance', 'running', 'cn-shanghai', '4C8G', 'mock', 'pod-042', 'cloud'),
            (16, 10, 'account-db-mysql', 'database', 'running', 'cn-shanghai', 'db.r6g.xlarge', 'mock', 'rds-004', 'cloud'),
            # 数据仓库资源
            (17, 11, 'dw-worker-pod-1', 'instance', 'running', 'cn-beijing', '8C16G', 'mock', 'pod-051', 'cloud'),
            (18, 11, 'dw-worker-pod-2', 'instance', 'running', 'cn-beijing', '8C16G', 'mock', 'pod-052', 'cloud'),
            (19, 11, 'dw-storage', 'database', 'running', 'cn-beijing', '10TB', 'mock', 'oss-001', 'cloud'),
            # 监控系统资源
            (20, 13, 'prometheus-pod', 'instance', 'running', 'cn-hangzhou', '4C8G', 'mock', 'pod-061', 'cloud'),
            (21, 13, 'grafana-pod', 'instance', 'running', 'cn-hangzhou', '2C4G', 'mock', 'pod-062', 'cloud'),
            # 日志平台资源
            (22, 14, 'elasticsearch-pod-1', 'instance', 'running', 'cn-hangzhou', '8C16G', 'mock', 'pod-071', 'cloud'),
            (23, 14, 'elasticsearch-pod-2', 'instance', 'running', 'cn-hangzhou', '8C16G', 'mock', 'pod-072', 'cloud'),
            (24, 14, 'elasticsearch-pod-3', 'instance', 'running', 'cn-hangzhou', '8C16G', 'mock', 'pod-073', 'cloud'),
            (25, 14, 'kibana-pod', 'instance', 'running', 'cn-hangzhou', '2C4G', 'mock', 'pod-074', 'cloud'),
            # 运维工具资源
            (26, 15, 'ops-api-pod', 'instance', 'running', 'cn-hangzhou', '2C4G', 'mock', 'pod-081', 'cloud'),
            (27, 15, 'ops-scheduler-pod', 'instance', 'running', 'cn-hangzhou', '2C4G', 'mock', 'pod-082', 'cloud'),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_resource 
               (id, environment_id, name, resource_type, status, region, spec, provider, cloud_id, managed_by) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            resources
        )
        
        # 资源关系
        resource_relations = [
            # 订单API Pod 属于订单服务
            (1, 1, 4, 'deployed_on', 'hard', None),
            (2, 2, 4, 'deployed_on', 'hard', None),
            (3, 3, 4, 'deployed_on', 'hard', None),
            # 用户API Pod 属于用户服务
            (4, 5, 8, 'deployed_on', 'hard', None),
            (5, 6, 8, 'deployed_on', 'hard', None),
            # 支付API Pod 属于支付服务
            (6, 9, 11, 'deployed_on', 'hard', None),
            (7, 10, 11, 'deployed_on', 'hard', None),
            # 支付网关 Pod 属于支付网关
            (8, 12, 11, 'deployed_on', 'hard', None),
            (9, 13, 11, 'deployed_on', 'hard', None),
            # 账务API Pod 属于账务服务
            (10, 14, 16, 'deployed_on', 'hard', None),
            (11, 15, 16, 'deployed_on', 'hard', None),
            # 数据仓库 Pod 属于数据仓库
            (12, 17, 19, 'deployed_on', 'hard', None),
            (13, 18, 19, 'deployed_on', 'hard', None),
            # 监控系统 Pod
            (14, 20, 21, 'deployed_on', 'hard', None),
            (15, 21, 22, 'deployed_on', 'hard', None),
            # 日志平台 Pod
            (16, 22, 23, 'deployed_on', 'hard', None),
            (17, 23, 24, 'deployed_on', 'hard', None),
            (18, 24, 25, 'deployed_on', 'hard', None),
            (19, 25, 26, 'deployed_on', 'hard', None),
            # 运维工具 Pod
            (20, 26, 27, 'deployed_on', 'hard', None),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_resource_relation 
               (id, source_resource_id, target_resource_id, relation_type, strength, metadata) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            resource_relations
        )
        
        conn.commit()
        conn.close()
    
    def _seed_deployment_units(self, environments: dict):
        """填充部署单元数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        deployment_units = [
            (1, 'order-api-deployment', 'k8s', '4C8G', 3, 45.2, 62.1, 'running'),
            (1, 'order-worker-deployment', 'k8s', '4C8G', 2, 23.5, 45.3, 'running'),
            (4, 'user-api-deployment', 'k8s', '4C8G', 2, 38.7, 55.2, 'running'),
            (6, 'pay-api-deployment', 'k8s', '4C8G', 2, 42.1, 58.9, 'running'),
            (6, 'pay-worker-deployment', 'k8s', '2C4G', 1, 15.3, 32.1, 'running'),
            (8, 'pay-gw-deployment', 'k8s', '2C4G', 2, 28.4, 41.2, 'running'),
            (10, 'account-api-deployment', 'k8s', '4C8G', 2, 35.6, 52.3, 'running'),
            (11, 'dw-worker-deployment', 'k8s', '8C16G', 3, 65.2, 78.4, 'running'),
            (13, 'prometheus-deployment', 'k8s', '4C8G', 1, 45.2, 62.1, 'running'),
            (13, 'grafana-deployment', 'k8s', '2C4G', 1, 12.3, 28.5, 'running'),
            (14, 'elasticsearch-deployment', 'k8s', '8C16G', 3, 72.1, 85.3, 'running'),
            (14, 'kibana-deployment', 'k8s', '2C4G', 1, 15.2, 32.1, 'running'),
            (15, 'ops-api-deployment', 'k8s', '2C4G', 1, 18.5, 35.2, 'running'),
            (15, 'ops-scheduler-deployment', 'k8s', '2C4G', 1, 12.1, 28.3, 'running'),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_deployment_unit 
               (environment_id, name, unit_type, spec, instance_count, cpu_usage, memory_usage, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            deployment_units
        )
        
        conn.commit()
        conn.close()
    
    def _seed_change_records(self):
        """填充变更记录数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        change_records = [
            ('TK-2026-001', '添加订单服务到用户服务依赖', 'relation_add', 1, 6, 'service', 'service',
             None, '{"protocol": "HTTP", "port": 8081}', 'executed', 'admin',
             (datetime.now() - timedelta(days=7)).isoformat(), (datetime.now() - timedelta(days=7)).isoformat()),
            ('TK-2026-002', '修改支付网关超时配置', 'relation_update', 7, 10, 'service', 'service',
             '{"timeout_ms": 3000}', '{"timeout_ms": 5000}', 'executed', 'admin',
             (datetime.now() - timedelta(days=5)).isoformat(), (datetime.now() - timedelta(days=5)).isoformat()),
            ('TK-2026-003', '添加监控系统到Grafana依赖', 'relation_add', 22, 21, 'service', 'service',
             None, '{"protocol": "HTTP", "port": 9090}', 'executed', 'ops',
             (datetime.now() - timedelta(days=3)).isoformat(), (datetime.now() - timedelta(days=3)).isoformat()),
            ('TK-2026-004', '更新订单服务实例数', 'instance_scale', 1, None, 'service', None,
             '{"instance_count": 2}', '{"instance_count": 3}', 'executed', 'admin',
             (datetime.now() - timedelta(days=1)).isoformat(), (datetime.now() - timedelta(days=1)).isoformat()),
            ('TK-2026-005', '添加测试环境订单服务依赖', 'relation_add', 4, 9, 'service', 'service',
             None, '{"protocol": "HTTP", "port": 8081, "strength": "soft"}', 'pending', 'dev',
             datetime.now().isoformat(), None),
        ]
        
        cursor.executemany(
            '''INSERT INTO mock_change_record 
               (ticket_no, title, change_type, source_id, target_id, source_type, target_type,
                old_value, new_value, status, operator, created_at, executed_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            change_records
        )
        
        conn.commit()
        conn.close()


def seed_mock_data():
    """种子函数：填充 Mock 数据"""
    seeder = MockDataSeeder()
    seeder.run()


if __name__ == '__main__':
    seed_mock_data()