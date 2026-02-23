# ──────────────────────────────────────────────────────────────
# JeyaRamaDesk — Enterprise Customer Support Platform
# Django Settings Configuration
# ──────────────────────────────────────────────────────────────

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'oq138oq8$an2pw&@_llh=)xz6jn53fqyu8z&j)rawa13gsj&i@'
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.2.76,jeyarama.com,www.jeyarama.com').split(',')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Application Registry ─────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    # Daphne ASGI server — must be before staticfiles
    'daphne',

    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'channels',
    'django_extensions',

    # django-allauth (Google OAuth)
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # JeyaRamaDesk apps
    'accounts.apps.AccountsConfig',
    'tickets.apps.TicketsConfig',
    'sla.apps.SlaConfig',
    'automation.apps.AutomationConfig',
    'knowledge_base.apps.KnowledgeBaseConfig',
    'reports.apps.ReportsConfig',
    'dashboard.apps.DashboardConfig',
    'notifications.apps.NotificationsConfig',
    'livechat.apps.LivechatConfig',
]

# ── Middleware Stack ──────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'jeyaramadesk.middleware.audit.AuditMiddleware',
    'jeyaramadesk.middleware.rate_limit.RateLimitMiddleware',
]

ROOT_URLCONF = 'jeyaramadesk.urls'

# ── Templates ─────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'jeyaramadesk.wsgi.application'
ASGI_APPLICATION = 'jeyaramadesk.asgi.application'

# ── Database ──────────────────────────────────────────────────
# Default: SQLite for dev. Set DB_ENGINE env var for MySQL in production.
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

# ── Custom User Model ────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

# ── Password Validation ──────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalization ─────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

URL_PREFIX = '/desk'

# --- Force Script to redirect to /desk -----------------------
# FORCE_SCRIPT_NAME = '/desk'

# If using Django Admin, consider setting:
# ADMIN_URL = "/desk/admin/"

CSRF_TRUSTED_ORIGINS = [
    "https://jeyarama.com",
    "https://www.jeyarama.com",
]

# ── Static & Media Files ─────────────────────────────────────
STATIC_URL = '/desk/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/desk/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Default Primary Key ──────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Django REST Framework ─────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
    },
}

# ── JWT Settings ──────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── Channels (WebSocket) ─────────────────────────────────────
ASGI_APPLICATION = 'jeyaramadesk.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': os.environ.get(
            'CHANNEL_BACKEND',
            'channels.layers.InMemoryChannelLayer'
        ),
        'CONFIG': {},
    }
}

# ── Celery Configuration ─────────────────────────────────────
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_BEAT_SCHEDULE = {
    'check-sla-breaches': {
        'task': 'sla.tasks.check_sla_breaches',
        'schedule': 300.0,
    },
    'run-automation-rules': {
        'task': 'automation.tasks.run_scheduled_automations',
        'schedule': 60.0,
    },
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'support@jeyaramadesk.com')

# ── File Upload ───────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.txt', '.csv', '.zip',
]
MAX_UPLOAD_SIZE_MB = 10

# ── Logging ───────────────────────────────────────────────────
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}.{funcName}:{lineno} — {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} — {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'jeyaramadesk.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'errors.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'jeyaramadesk': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ── Login / Redirect URLs ────────────────────────────────────
LOGIN_URL = '/desk/accounts/login/'
LOGIN_REDIRECT_URL = '/desk/'
LOGOUT_REDIRECT_URL = '/desk/accounts/login/'
SOCIALACCOUNT_LOGIN_REDIRECT_URL = '/desk/'

# ── django-allauth / Google OAuth ─────────────────────────────
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# allauth account settings
ACCOUNT_LOGIN_METHODS = {'email'}          # login by email only
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # email required, no username
ACCOUNT_EMAIL_VERIFICATION = 'none'        # skip email verification for fast onboarding
ACCOUNT_SIGNUP_REDIRECT_URL = '/desk/'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None   # our User model has no username field
ACCOUNT_ADAPTER = 'accounts.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.SocialAccountAdapter'
SOCIALACCOUNT_LOGIN_ON_GET = True          # skip the "Continue?" intermediate page

# Google OAuth2 provider configuration
# Credentials are managed via Django admin → Social Applications
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
}

# ── Security Hardening (production) ──────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True


# Cookie paths - CRITICAL for subpath deployment
SESSION_COOKIE_PATH = '/desk/'
CSRF_COOKIE_PATH = '/desk/'

# Unique cookie names - CRITICAL when multiple apps on same domain
SESSION_COOKIE_NAME = 'desk_sessionid'
CSRF_COOKIE_NAME = 'desk_csrftoken'
