"""
CMDB 服务工厂：根据配置返回 Mock 或真实数据服务
"""
from django.conf import settings


def get_cmdb_service():
    """
    获取 CMDB 服务实例
    
    根据 USE_MOCK_DATA 配置返回不同的服务实现：
    - MockService: 使用 SQLite 数据库的模拟数据服务
    - RealService: 使用真实数据库的服务（待实现）
    """
    if getattr(settings, 'USE_MOCK_DATA', True):
        # 使用 Mock 数据服务
        from mock_data.service import MockService
        return MockService(db_path=getattr(settings, 'MOCK_DB_PATH', None))
    else:
        # 使用真实数据服务（待实现）
        # from cmdb.real_service import RealService
        # return RealService()
        raise NotImplementedError("真实数据服务尚未实现")