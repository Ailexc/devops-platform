"""
Celery 应用配置（Demo 简化版）
不使用 Celery，任务直接同步执行
"""
import os

# 设置 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


class MockCeleryApp:
    """模拟 Celery App，使代码兼容但不实际执行异步任务"""
    
    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    
    def config_from_object(self, *args, **kwargs):
        pass
    
    def autodiscover_tasks(self, *args, **kwargs):
        pass


app = MockCeleryApp()
