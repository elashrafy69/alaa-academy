"""
إعدادات الإنتاج
"""

from .settings import *
import os
from decouple import config

# إعدادات الإنتاج
DEBUG = False

# المضيفون المسموحون
ALLOWED_HOSTS = [
    'marketwise-academy-qhizq.web.app',
    'marketwise-academy-qhizq.firebaseapp.com',
    'localhost',
    '127.0.0.1',
]

# قاعدة البيانات للإنتاج
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# إعدادات الأمان للإنتاج
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# إعدادات الجلسات والكوكيز
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# إعدادات البريد الإلكتروني
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@marketwise-academy.com')

# إعدادات الملفات الثابتة
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# إعدادات إضافية للملفات الثابتة
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# إعدادات الملفات المرفوعة
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# إعدادات Firebase Storage للملفات
FIREBASE_STORAGE_BUCKET = config('FIREBASE_STORAGE_BUCKET')

# إعدادات Supabase للإنتاج
SUPABASE_URL = config('SUPABASE_URL')
SUPABASE_KEY = config('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY')

# إعدادات Firebase للإنتاج
FIREBASE_CONFIG = {
    'apiKey': config('FIREBASE_API_KEY'),
    'authDomain': config('FIREBASE_AUTH_DOMAIN'),
    'projectId': config('FIREBASE_PROJECT_ID'),
    'storageBucket': config('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': config('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': config('FIREBASE_APP_ID'),
}

# إعدادات CORS للإنتاج
CORS_ALLOWED_ORIGINS = [
    "https://marketwise-academy-qhizq.web.app",
    "https://marketwise-academy-qhizq.firebaseapp.com",
]

CORS_ALLOW_CREDENTIALS = True

# إعدادات التخزين المؤقت
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'alaa_academy',
        'TIMEOUT': 300,
    }
}

# إعدادات الجلسات
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# إعدادات التسجيل للإنتاج
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/security.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'courses': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# إعدادات الأداء
USE_TZ = True
USE_I18N = True
USE_L10N = True

# إعدادات قاعدة البيانات للأداء
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 20,
    'OPTIONS': {
        'MAX_CONNS': 20,
    }
})

# ضغط الاستجابات
MIDDLEWARE.insert(1, 'django.middleware.gzip.GZipMiddleware')

# إعدادات الملفات الثابتة المتقدمة
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# إعدادات أمان إضافية
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# إعدادات رفع الملفات للإنتاج
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# إعدادات المهام المجدولة (إذا كنت تستخدم Celery)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# إعدادات المراقبة والتنبيهات
ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@marketwise-academy.com')),
]

MANAGERS = ADMINS

# إعدادات الخطأ 500
SERVER_EMAIL = config('SERVER_EMAIL', default='server@marketwise-academy.com')

# إعدادات إضافية للأمان
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# تعطيل بعض الميزات في الإنتاج
INTERNAL_IPS = []  # تعطيل Django Debug Toolbar

# إعدادات المنطقة الزمنية
TIME_ZONE = 'Asia/Riyadh'
LANGUAGE_CODE = 'ar'

# إعدادات الترجمة
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# إعدادات النسخ الاحتياطي
BACKUP_ENABLED = True
BACKUP_SCHEDULE = '0 2 * * *'  # يومياً في الساعة 2 صباحاً

# إعدادات المراقبة
MONITORING_ENABLED = True
HEALTH_CHECK_URL = '/health/'

# إعدادات الأداء المتقدمة
CONN_MAX_AGE = 60
ATOMIC_REQUESTS = True

# إعدادات الذاكرة
CACHES['default']['OPTIONS']['COMPRESSOR'] = 'django_redis.compressors.zlib.ZlibCompressor'
