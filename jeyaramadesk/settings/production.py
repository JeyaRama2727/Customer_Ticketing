# ──────────────────────────────────────────────────────────────
# JeyaRamaDesk — Production Settings
# Usage:  DJANGO_ENV=production
# All secrets MUST come from environment variables.
# ──────────────────────────────────────────────────────────────

import os
from .base import *  # noqa: F401,F403

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']       # required in production
DEBUG = False
ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'jeyarama.com,www.jeyarama.com',
).split(',')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Database (MySQL — production) ────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'desk_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
        },
    }
}

# ── Channels (Redis for production) ──────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': os.environ.get(
            'CHANNEL_BACKEND',
            'channels_redis.core.RedisChannelLayer',
        ),
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://localhost:6379/1')],
        },
    }
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://jeyarama.com,https://www.jeyarama.com',
).split(',')

# ── Email (SMTP in production) ───────────────────────────────
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'support@jeyaramadesk.com')

# ── Security Hardening ───────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
