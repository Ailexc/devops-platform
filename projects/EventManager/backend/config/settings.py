"""
Django settings for event_manager project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,event.local,event-api.local").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "django_celery_results",
    # Local apps
    "apps.event_store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS — 由 Traefik 网关层统一处理，Django 不再管理

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
# 优先使用 PostgreSQL (Docker)，回退到 SQLite (本地开发)
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL and DATABASE_URL.startswith("postgres"):
    _db_parts = DATABASE_URL.split("://")[1].split("@")
    _db_creds = _db_parts[0].split(":")
    _db_host = _db_parts[1].split(":")
    _db_hostname = _db_host[0]
    _db_port = _db_host[1].split("/")[0] if "/" in _db_host[1] else _db_host[1]
    _db_name = _db_host[1].split("/")[1] if "/" in _db_host[1] else "eventdb"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", _db_name),
            "USER": os.getenv("DB_USER", _db_creds[0]),
            "PASSWORD": os.getenv("DB_PASSWORD", _db_creds[1]),
            "HOST": os.getenv("DB_HOST", _db_hostname),
            "PORT": os.getenv("DB_PORT", _db_port),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Redis / Cache
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery (主要设置由 celery_app.py 根据 broker 可用性自动配置)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SOFT_TIME_LIMIT = 60  # seconds
CELERY_TASK_TIME_LIMIT = 120  # seconds
# 统一消息队列规范：Event 系统任务全部进专属队列 event（与 Task 系统隔离）
CELERY_TASK_DEFAULT_QUEUE = "event"
CELERY_TASK_DEFAULT_EXCHANGE = "event"
CELERY_TASK_DEFAULT_ROUTING_KEY = "event"

# Internationalization
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
