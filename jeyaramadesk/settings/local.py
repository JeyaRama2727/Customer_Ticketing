# ──────────────────────────────────────────────────────────────
# JeyaRamaDesk — Local / Development Settings
# Usage:  DJANGO_ENV=local  (or just leave it unset — default)
# ──────────────────────────────────────────────────────────────

from .base import *  # noqa: F401,F403

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = 'oq138oq8$an2pw&@_llh=)xz6jn53fqyu8z&j)rawa13gsj&i@'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.2.76']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Database (MySQL — local) ─────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'desk_db',
        'USER': 'root',
        'PASSWORD': 'root@2001',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
        },
    }
}

# ── Channels (in-memory for dev) ─────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        'CONFIG': {},
    }
}

# ── CORS (allow all in dev) ──────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ── Email (print to console in dev) ──────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
