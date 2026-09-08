"""
Mock 数据服务层：提供对 Mock 数据库的访问和操作
用于 Demo 阶段的 CMDB 数据模拟
"""
import sqlite3
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServiceRelation:
    """服务依赖关系数据类"""
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
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认使用 mock_data 目录下的 mock.db
            base_dir = Path(__file__).parent
            self.db_path = str(base_dir / 'mock.db')
        else:
            self.db_path = db_path
        self._conn = None
    
    @property
    def conn(self):
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # 启用外键约束
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ==================== 部门相关 ====================
    
    def get_departments(self) -> List[Dict]:
        """获取所有部门"""
        query = '''
            SELECT d.*, 
                   p.name as parent_name,
                   (SELECT COUNT(*) FROM mock_application a WHERE a.department_id = d.id) as app_count
            FROM mock_department d
            LEFT JOIN mock_department p ON d.parent_id = p.id
            ORDER BY d.sort_order, d.id
        '''
        rows = self.conn.execute(query).fetchall()
        return [dict(row) for row in rows]
    
    def get_department_tree(self) -> List[Dict]:
        """获取部门树结构"""
        departments = self.get_departments()
        dept_map = {d['id']: d for d in departments}
        tree = []
        for dept in departments:
            dept['children'] = []
            if dept['parent_id'] and dept['parent_id'] in dept_map:
                dept_map[dept['parent_id']]['children'].append(dept)
            else:
                tree.append(dept)
        return tree
    
    # ==================== 应用相关 ====================
    
    def get_applications(self, department_id: int = None) -> List[Dict]:
        """获取应用列表"""
        query = '''
            SELECT a.*, 
                   d.name as department_name,
                   (SELECT COUNT(*) FROM mock_environment e WHERE e.application_id = a.id) as env_count
            FROM mock_application a
            LEFT JOIN mock_department d ON a.department_id = d.id
        '''
        params = []
        if department_id:
            query += ' WHERE a.department_id = ?'
            params.append(department_id)
        query += ' ORDER BY a.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_application_detail(self, app_id: int) -> Optional[Dict]:
        """获取应用详情"""
        query = '''
            SELECT a.*, 
                   d.name as department_name
            FROM mock_application a
            LEFT JOIN mock_department d ON a.department_id = d.id
            WHERE a.id = ?
        '''
        row = self.conn.execute(query, (app_id,)).fetchone()
        if row:
            app = dict(row)
            # 获取环境列表
            app['environments'] = self.get_environments(app_id)
            return app
        return None
    
    # ==================== 环境相关 ====================
    
    def get_environments(self, application_id: int = None) -> List[Dict]:
        """获取环境列表"""
        query = '''
            SELECT e.*, 
                   a.name as application_name,
                   (SELECT COUNT(*) FROM mock_service s WHERE s.environment_id = e.id) as services_count
            FROM mock_environment e
            LEFT JOIN mock_application a ON e.application_id = a.id
        '''
        params = []
        if application_id:
            query += ' WHERE e.application_id = ?'
            params.append(application_id)
        query += ' ORDER BY e.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_environment_detail(self, env_id: int) -> Optional[Dict]:
        """获取环境详情"""
        query = '''
            SELECT e.*, 
                   a.name as application_name,
                   a.app_code
            FROM mock_environment e
            LEFT JOIN mock_application a ON e.application_id = a.id
            WHERE e.id = ?
        '''
        row = self.conn.execute(query, (env_id,)).fetchone()
        if row:
            env = dict(row)
            # 获取服务列表
            env['services'] = self.get_services(env_id)
            return env
        return None
    
    # ==================== 服务相关 ====================
    
    def get_services(self, environment_id: int = None) -> List[Dict]:
        """获取服务列表"""
        query = '''
            SELECT s.*, 
                   e.name as environment_name,
                   a.name as application_name
            FROM mock_service s
            LEFT JOIN mock_environment e ON s.environment_id = e.id
            LEFT JOIN mock_application a ON e.application_id = a.id
        '''
        params = []
        if environment_id:
            query += ' WHERE s.environment_id = ?'
            params.append(environment_id)
        query += ' ORDER BY s.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_service_detail(self, service_id: int) -> Optional[Dict]:
        """获取服务详情"""
        query = '''
            SELECT s.*, 
                   e.name as environment_name,
                   a.name as application_name,
                   a.app_code
            FROM mock_service s
            LEFT JOIN mock_environment e ON s.environment_id = e.id
            LEFT JOIN mock_application a ON e.application_id = a.id
            WHERE s.id = ?
        '''
        row = self.conn.execute(query, (service_id,)).fetchone()
        if row:
            svc = dict(row)
            # 获取端点
            svc['endpoints'] = self.get_service_endpoints(service_id)
            # 获取依赖关系
            svc['dependencies'] = self.get_service_dependencies(service_id)
            return svc
        return None
    
    def get_service_endpoints(self, service_id: int) -> List[Dict]:
        """获取服务端点"""
        query = '''
            SELECT * FROM mock_service_endpoint
            WHERE service_id = ?
            ORDER BY id
        '''
        rows = self.conn.execute(query, (service_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_service_dependencies(self, service_id: int) -> List[Dict]:
        """获取服务的所有依赖关系"""
        query = '''
            SELECT r.*, 
                   ss.name as source_name,
                   ts.name as target_name
            FROM mock_service_relation r
            JOIN mock_service ss ON r.source_service_id = ss.id
            JOIN mock_service ts ON r.target_service_id = ts.id
            WHERE r.source_service_id = ? OR r.target_service_id = ?
        '''
        rows = self.conn.execute(query, (service_id, service_id)).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== 关系相关 ====================
    
    def get_relations(self, environment_id: int = None) -> List[Dict]:
        """获取所有关系"""
        query = '''
            SELECT r.*, 
                   ss.name as source_name, ss.service_type as source_type,
                   ts.name as target_name, ts.service_type as target_type
            FROM mock_service_relation r
            JOIN mock_service ss ON r.source_service_id = ss.id
            JOIN mock_service ts ON r.target_service_id = ts.id
            JOIN mock_environment se ON ss.environment_id = se.id
            JOIN mock_environment te ON ts.environment_id = te.id
        '''
        params = []
        if environment_id:
            query += ' WHERE se.id = ? OR te.id = ?'
            params.extend([environment_id, environment_id])
        query += ' ORDER BY r.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_relation_detail(self, relation_id: int) -> Optional[Dict]:
        """获取关系详情"""
        query = '''
            SELECT r.*, 
                   ss.name as source_name, ss.port as source_port,
                   ts.name as target_name, ts.port as target_port
            FROM mock_service_relation r
            JOIN mock_service ss ON r.source_service_id = ss.id
            JOIN mock_service ts ON r.target_service_id = ts.id
            WHERE r.id = ?
        '''
        row = self.conn.execute(query, (relation_id,)).fetchone()
        return dict(row) if row else None
    
    def create_relation(self, data: Dict) -> int:
        """创建新的依赖关系"""
        query = '''
            INSERT INTO mock_service_relation 
            (source_service_id, target_service_id, relation_type, strength, protocol, port,
             source_domain, source_port, target_domain, target_port,
             load_balance, timeout_ms, retry_count, retry_interval_ms,
             auth_type, rate_limit, tracing_enabled, metrics_enabled,
             critical_level, sla_target, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor = self.conn.execute(query, (
            data['source_service_id'],
            data['target_service_id'],
            data.get('relation_type', 'depends_on'),
            data.get('strength', 'hard'),
            data.get('protocol', 'HTTP'),
            data.get('port'),
            data.get('source_domain'),
            data.get('source_port'),
            data.get('target_domain'),
            data.get('target_port'),
            data.get('load_balance', 'round_robin'),
            data.get('timeout_ms', 3000),
            data.get('retry_count', 3),
            data.get('retry_interval_ms', 100),
            data.get('auth_type', 'none'),
            data.get('rate_limit'),
            data.get('tracing_enabled', True),
            data.get('metrics_enabled', True),
            data.get('critical_level', 'important'),
            data.get('sla_target'),
            data.get('status', 'active'),
            data.get('created_by')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_relation(self, relation_id: int, data: Dict) -> bool:
        """更新依赖关系"""
        # 构建动态更新语句
        set_clauses = []
        params = []
        for key, value in data.items():
            if key != 'id':  # 不允许更新ID
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(relation_id)
        
        query = f'''
            UPDATE mock_service_relation
            SET {', '.join(set_clauses)}
            WHERE id = ?
        '''
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_relation(self, relation_id: int) -> bool:
        """删除依赖关系"""
        query = 'DELETE FROM mock_service_relation WHERE id = ?'
        cursor = self.conn.execute(query, (relation_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== 图谱相关 ====================
    
    def get_environment_graph(self, env_id: int) -> Dict:
        """获取环境的完整图谱数据"""
        nodes = self._get_nodes(env_id)
        edges = self._get_edges(env_id)
        return {'nodes': nodes, 'edges': edges}
    
    def get_application_graph(self, app_id: int, environment_id: int = None) -> Dict:
        """获取应用的完整图谱数据"""
        if environment_id:
            # 指定环境
            return self.get_environment_graph(environment_id)
        
        # 获取应用下所有环境
        environments = self.get_environments(app_id)
        all_nodes = []
        all_edges = []
        seen_node_ids = set()
        
        for env in environments:
            env_graph = self.get_environment_graph(env['id'])
            for node in env_graph['nodes']:
                if node['id'] not in seen_node_ids:
                    all_nodes.append(node)
                    seen_node_ids.add(node['id'])
            all_edges.extend(env_graph['edges'])
        
        return {'nodes': all_nodes, 'edges': all_edges}
    
    def _get_nodes(self, env_id: int) -> List[Dict]:
        """获取环境的所有节点"""
        nodes = []
        
        # 环境节点
        env = self.get_environment_detail(env_id)
        if env:
            nodes.append({
                'id': f"env:{env_id}",
                'name': env['name'],
                'category': 'environment',
                'meta': {
                    'env_type': env.get('env_type'),
                    'application': env.get('application_name'),
                    'region': env.get('region')
                }
            })
        
        # 服务节点
        services = self.get_services(env_id)
        for svc in services:
            nodes.append({
                'id': f"svc:{svc['id']}",
                'name': svc['name'],
                'category': 'service',
                'meta': {
                    'service_type': svc.get('service_type'),
                    'deploy_type': svc.get('deploy_type'),
                    'status': svc.get('status'),
                    'port': svc.get('port'),
                    'instance_count': svc.get('instance_count', 1)
                }
            })
        
        return nodes
    
    def _get_edges(self, env_id: int) -> List[Dict]:
        """获取环境的所有边"""
        edges = []
        
        # 获取服务依赖关系
        relations = self.get_relations(env_id)
        for rel in relations:
            edges.append({
                'id': rel['id'],
                'source': f"svc:{rel['source_service_id']}",
                'target': f"svc:{rel['target_service_id']}",
                'relation_type': rel['relation_type'],
                'strength': rel['strength'],
                'metadata': {
                    'protocol': rel.get('protocol'),
                    'port': rel.get('port'),
                    'source_domain': rel.get('source_domain'),
                    'target_domain': rel.get('target_domain'),
                    'load_balance': rel.get('load_balance'),
                    'timeout_ms': rel.get('timeout_ms'),
                    'retry_count': rel.get('retry_count'),
                    'auth_type': rel.get('auth_type'),
                    'tracing_enabled': rel.get('tracing_enabled'),
                    'critical_level': rel.get('critical_level')
                }
            })
        
        return edges
    
    # ==================== 资源相关 ====================
    
    def get_resources(self, environment_id: int = None, resource_type: str = None) -> List[Dict]:
        """获取资源列表"""
        query = '''
            SELECT r.*, 
                   e.name as environment_name
            FROM mock_resource r
            LEFT JOIN mock_environment e ON r.environment_id = e.id
        '''
        params = []
        conditions = []
        
        if environment_id:
            conditions.append('r.environment_id = ?')
            params.append(environment_id)
        if resource_type:
            conditions.append('r.resource_type = ?')
            params.append(resource_type)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY r.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== 部署单元相关 ====================
    
    def get_deployment_units(self, environment_id: int = None) -> List[Dict]:
        """获取部署单元"""
        query = '''
            SELECT du.*, 
                   e.name as environment_name
            FROM mock_deployment_unit du
            LEFT JOIN mock_environment e ON du.environment_id = e.id
        '''
        params = []
        if environment_id:
            query += ' WHERE du.environment_id = ?'
            params.append(environment_id)
        query += ' ORDER BY du.id'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    # ==================== 变更记录相关 ====================
    
    def get_change_records(self, ticket_no: str = None) -> List[Dict]:
        """获取变更记录"""
        query = 'SELECT * FROM mock_change_record'
        params = []
        if ticket_no:
            query += ' WHERE ticket_no = ?'
            params.append(ticket_no)
        query += ' ORDER BY created_at DESC'
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def create_change_record(self, data: Dict) -> int:
        """创建变更记录"""
        query = '''
            INSERT INTO mock_change_record 
            (ticket_no, title, change_type, source_id, target_id, 
             source_type, target_type, old_value, new_value, status, operator)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor = self.conn.execute(query, (
            data.get('ticket_no'),
            data.get('title'),
            data.get('change_type'),
            data.get('source_id'),
            data.get('target_id'),
            data.get('source_type'),
            data.get('target_type'),
            data.get('old_value'),
            data.get('new_value'),
            data.get('status', 'pending'),
            data.get('operator')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    # ==================== 统计相关 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {}
        
        # 部门统计
        stats['departments'] = self.conn.execute('SELECT COUNT(*) FROM mock_department').fetchone()[0]
        
        # 应用统计
        stats['applications'] = self.conn.execute('SELECT COUNT(*) FROM mock_application').fetchone()[0]
        
        # 环境统计
        stats['environments'] = self.conn.execute('SELECT COUNT(*) FROM mock_environment').fetchone()[0]
        
        # 服务统计
        stats['services'] = self.conn.execute('SELECT COUNT(*) FROM mock_service').fetchone()[0]
        
        # 关系统计
        stats['relations'] = self.conn.execute('SELECT COUNT(*) FROM mock_service_relation').fetchone()[0]
        
        # 资源统计
        stats['resources'] = self.conn.execute('SELECT COUNT(*) FROM mock_resource').fetchone()[0]
        
        # 按类型统计服务
        service_types = self.conn.execute('''
            SELECT service_type, COUNT(*) as count
            FROM mock_service
            GROUP BY service_type
        ''').fetchall()
        stats['services_by_type'] = {row[0]: row[1] for row in service_types}
        
        # 按类型统计资源
        resource_types = self.conn.execute('''
            SELECT resource_type, COUNT(*) as count
            FROM mock_resource
            GROUP BY resource_type
        ''').fetchall()
        stats['resources_by_type'] = {row[0]: row[1] for row in resource_types}
        
        return stats


# 便捷函数
def get_mock_service(db_path: str = None) -> MockService:
    """获取 MockService 实例"""
    return MockService(db_path)