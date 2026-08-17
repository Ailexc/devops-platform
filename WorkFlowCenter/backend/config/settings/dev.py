"""
Development settings for workflow project.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = [
    'api.workflow.orb.local',
    'frontend.workflow.orb.local',
    '*',
]

# Allow simpler password validation in dev
AUTH_PASSWORD_VALIDATORS = []

# Log SQL queries in dev
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
    },
}
