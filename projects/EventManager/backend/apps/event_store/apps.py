from django.apps import AppConfig


class EventStoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.event_store"
    verbose_name = "事件存储"

    def ready(self):
        """Django 就绪后注册内置 Handler"""
        import handlers  # noqa: F401
