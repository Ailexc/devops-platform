from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # 幂等初始化：能力层 discover + 配置层播种 + 调度层预建
        # 表未就绪（migrate 期间）会自动跳过，安全。
        try:
            from .startup import initialize
            initialize()
        except Exception:
            # ready() 中绝不能抛异常，否则 runserver/migrate 启动失败
            pass
