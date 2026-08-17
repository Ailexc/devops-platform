import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("event_manager")

# 检测是否有可用的 Broker（RabbitMQ / Redis）
_broker_env = os.environ.get("CELERY_BROKER_URL", "")
if _broker_env:
    # 有外部 Broker — 正常分布式模式
    app.conf.broker_url = _broker_env
    app.conf.result_backend = "django-db"
    app.conf.task_always_eager = False
else:
    # 无外部 Broker — Demo 模式：同步执行 + memory 传输
    app.conf.broker_url = "memory://localhost/"
    app.conf.result_backend = "cache+memory://"
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True

app.config_from_object("django.conf:settings", namespace="CELERY", force=True)
app.autodiscover_tasks()
