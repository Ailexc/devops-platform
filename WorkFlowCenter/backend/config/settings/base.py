"""
Base settings for workflow project.
"""
import os
from pathlib import Path
from datetime import timedelta

# ---------------------------------------------------------------------------
# Path
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _get_env(key, default=''):
    """从环境变量获取配置，优先使用环境变量"""
    return os.environ.get(key, default)


SECRET_KEY = _get_env(
    'SECRET_KEY',
    'django-insecure-dev-key-change-in-production'
)

DEBUG = False

ALLOWED_HOSTS: list[str] = []

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'django_fsm',
    'django_fsm_log',

    # Project apps
    'apps.common',
    'apps.accounts',
    'apps.processes',
    'apps.capabilities',
    'apps.tickets',
    'apps.events',
    'apps.knowledge',
    'seed',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.common.middleware.IdempotencyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# Database（默认 SQLite 本地开发；设置 DATABASE_URL 时使用统一 PostgreSQL）
# ---------------------------------------------------------------------------
DATABASE_URL = _get_env('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres'):
    _db_url = DATABASE_URL.split('://')[1]
    _db_creds, _db_host = _db_url.split('@')
    _db_user, _db_pass = _db_creds.split(':')
    _db_hostport, _db_name = _db_host.split('/')
    _db_hostname = _db_hostport.split(':')[0]
    _db_port = _db_hostport.split(':')[1] if ':' in _db_hostport else '5432'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _db_name,
            'USER': _db_user,
            'PASSWORD': _db_pass,
            'HOST': _db_hostname,
            'PORT': _db_port,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
}

# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ---------------------------------------------------------------------------
# DRF Spectacular (OpenAPI 3.1)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'Workflow API',
    'DESCRIPTION': '工单系统 - 流程驱动的业务自动化平台',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1/',
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
# Celery：Demo 使用 eager 模式（同步执行，无需 broker）
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# AI 服务调用超时（秒）：MiMo 等大模型推理较慢，放宽到 120s
AI_REQUEST_TIMEOUT = 120

# ---------------------------------------------------------------------------
# AI 服务调用超时（秒）：MiMo 等大模型推理较慢，放宽到 120s
# ---------------------------------------------------------------------------
