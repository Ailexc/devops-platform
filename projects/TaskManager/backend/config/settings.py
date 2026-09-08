import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = bool(int(os.environ.get("DEBUG", "1")))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "drf_spectacular",
    "django_celery_beat",
    "django_celery_results",
    # Local apps
    "core.apps.CoreConfig",
    "orchestrator",
    "api.dashboard",
    "api.tasks",
    "api.config",
    "api.history",
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

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://cmdb:cmdb_dev@localhost:5432/cmdb")
import re
_db_match = re.match(r"postgres(?:ql)?://(.+):(.+)@(.+):(\d+)/(.+)", DATABASE_URL)
if _db_match:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _db_match.group(5),
            "USER": _db_match.group(1),
            "PASSWORD": _db_match.group(2),
            "HOST": _db_match.group(3),
            "PORT": _db_match.group(4),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# nginx 反代同源访问，无需 CORS

# Celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
# 统一消息队列：默认走环境变量 CELERY_BROKER_URL（RabbitMQ），兼容无配置时回退 Redis
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# DRF
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # 统一认证接入（方式二：直连认证中心 JWKS 验签统一 JWT）
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.unified_auth.UnifiedJWTAuthentication",
    ],
}

# drf-spectacular — OpenAPI 文档（供 Go 后端实现参考 / 契约对齐）
SPECTACULAR_SETTINGS = {
    "TITLE": "CMDB 任务管理平台 API",
    "DESCRIPTION": "任务树/执行历史/大盘统计/配置管理 接口契约（Python 版实现，Go 版按此对齐）",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
