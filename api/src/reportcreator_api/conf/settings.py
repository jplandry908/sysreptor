"""
Django settings for reportcreator_api project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import itertools
import json
import socket
import uuid
from datetime import timedelta
from pathlib import Path

import fido2.features
import redis
from csp.constants import NONE, SELF, UNSAFE_INLINE
from decouple import Csv, config
from kombu import Queue

from reportcreator_api.conf.plugins import load_plugins

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'data', cast=Path)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-ygvn9(x==kcv#r%pccf4rlzyz7_1v1b83$19&b2lsj6uz$mbro')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=False)

APPEND_SLASH = True


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sessions',

    'rest_framework',
    'django_filters',
    'adrf',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'simple_history',
    'channels',

    'reportcreator_api',
    'reportcreator_api.users',
    'reportcreator_api.pentests',
    'reportcreator_api.notifications',
    'reportcreator_api.tasks',
    'reportcreator_api.conf.admin.AdminConfig',
    'reportcreator_api.api_utils',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'reportcreator_api.utils.logging.RequestLoggingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'reportcreator_api.utils.middleware.ExtendSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'reportcreator_api.utils.middleware.AdminSessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'reportcreator_api.utils.middleware.CacheControlMiddleware',
    'reportcreator_api.utils.middleware.PermissionsPolicyMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'reportcreator_api.conf.urls'
WEBSOCKET_URLCONF = 'reportcreator_api.conf.urls_websocket'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend'],
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

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'reportcreator_api.users.auth.APITokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'reportcreator_api.utils.throttling.ScopedUserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'pdf': '3/10s',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'reportcreator_api.utils.api.exception_handler',
    'PAGE_SIZE': 100,
    'UNICODE_JSON': False,
}

# OpenAPI schema generator settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'SysReptor API',
    'VERSION': '0.0.0',
    'DESCRIPTION': 'Warning: This is an unstable API used by the SysReptor frontend. There might be breaking changes. Use at own risk.',
    'SERVE_PUBLIC': True,
    'SCHEMA_COERCE_PATH_PK_SUFFIX': True,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'ENUM_NAME_OVERRIDES': {
        'Language': 'reportcreator_api.pentests.models.Language',
        'ReviewStatus': 'reportcreator_api.pentests.models.ReviewStatus',
        'ProjectTypeScope': 'reportcreator_api.pentests.models.ProjectTypeScope',
        'ProjectTypeScopeCreate': ['global', 'private'],
    },
}


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': config('DATABASE_HOST', default=''),
        'PORT': config('DATABASE_PORT', default='5432'),
        'NAME': config('DATABASE_NAME', default=''),
        'USER': config('DATABASE_USER', default=''),
        'PASSWORD': config('DATABASE_PASSWORD', default=''),
        'DISABLE_SERVER_SIDE_CURSORS': True,
        'OPTIONS': {
            'prepare_threshold': None,
            'pool': True,
        },
    },
}



# Websockets
REDIS_URL = config('REDIS_URL', default=None)
DISABLE_WEBSOCKETS = config('DISABLE_WEBSOCKETS', cast=bool, default=False) or (not REDIS_URL)
if not DISABLE_WEBSOCKETS:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [{
                    'address': REDIS_URL,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {
                        socket.TCP_KEEPIDLE: 2,
                        socket.TCP_KEEPINTVL: 3,
                        socket.TCP_KEEPCNT: 5,
                    },
                    'retry_on_timeout': True,
                    'retry_on_error': [redis.ConnectionError],
                }],
            },
        },
    }
else:
    CHANNEL_LAYERS = {}



# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Login URL of SPA frontend
LOGIN_URL = '/login/'

SESSION_ENGINE = 'reportcreator_api.users.backends.session'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = timedelta(hours=14).seconds
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

MFA_SERVER_NAME = config('MFA_SERVER_NAME', default='SysReptor')
# FIDO2 RP ID: the domain name of the instance
MFA_FIDO2_RP_ID = config('MFA_FIDO2_RP_ID', default='')
MFA_LOGIN_TIMEOUT = timedelta(minutes=5)
SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT = timedelta(minutes=15)

fido2.features.webauthn_json_mapping.enabled = True


# Allowed Hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default='*')
if not MFA_FIDO2_RP_ID and len(ALLOWED_HOSTS) == 1 and '*' not in ALLOWED_HOSTS[0]:
    MFA_FIDO2_RP_ID = ALLOWED_HOSTS[0]

# Allow localhost. Required for docker healthchecks
ALLOWED_HOSTS += ['localhost', '127.0.0.1', '[::1]']
CSRF_TRUSTED_ORIGINS = list(itertools.chain(*map(lambda h: [f'https://{h}', f'http://{h}'], ALLOWED_HOSTS)))


# Authentication and OIDC settings
AUTHLIB_OAUTH_CLIENTS = {}
OIDC_AZURE_CLIENT_ID = config('OIDC_AZURE_CLIENT_ID', default=None)
OIDC_AZURE_CLIENT_SECRET = config('OIDC_AZURE_CLIENT_SECRET', default=None)
OIDC_AZURE_TENANT_ID = config('OIDC_AZURE_TENANT_ID', default=None)
if OIDC_AZURE_CLIENT_ID and OIDC_AZURE_CLIENT_SECRET and OIDC_AZURE_TENANT_ID:
    AUTHLIB_OAUTH_CLIENTS |= {
        'azure': {
            'label': 'Azure AD',
            'client_id': OIDC_AZURE_CLIENT_ID,
            'client_secret': OIDC_AZURE_CLIENT_SECRET,
            'server_metadata_url': f'https://login.microsoftonline.com/{OIDC_AZURE_TENANT_ID}/v2.0/.well-known/openid-configuration',
            'client_kwargs': {
                'scope': 'openid email profile',
                'code_challenge_method': 'S256',
            },
            'reauth_supported': True,
        },
    }

OIDC_GOOGLE_CLIENT_ID = config('OIDC_GOOGLE_CLIENT_ID', default=None)
OIDC_GOOGLE_CLIENT_SECRET = config('OIDC_GOOGLE_CLIENT_SECRET', default=None)
if OIDC_GOOGLE_CLIENT_ID and OIDC_GOOGLE_CLIENT_SECRET:
    AUTHLIB_OAUTH_CLIENTS |= {
        'google': {
            'label': 'Google',
            'client_id': OIDC_GOOGLE_CLIENT_ID,
            'client_secret': OIDC_GOOGLE_CLIENT_SECRET,
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
            'client_kwargs': {
                'scope': 'openid email profile',
                'code_challenge_method': 'S256',
            },
            'reauth_supported': False,
        },
    }

if oidc_config := config('OIDC_AUTHLIB_OAUTH_CLIENTS', cast=json.loads, default="{}"):
    AUTHLIB_OAUTH_CLIENTS |= oidc_config


REMOTE_USER_AUTH_ENABLED = config('REMOTE_USER_AUTH_ENABLED', cast=bool, default=False)
REMOTE_USER_AUTH_HEADER = config('REMOTE_USER_AUTH_HEADER', default='Remote-User')

LOCAL_USER_AUTH_ENABLED = config('LOCAL_USER_AUTH_ENABLED', cast=bool, default=True)

DEFAULT_AUTH_PROVIDER = config('DEFAULT_AUTH_PROVIDER', default=None)
DEFAULT_REAUTH_PROVIDER = config('DEFAULT_REAUTH_PROVIDER', default=DEFAULT_AUTH_PROVIDER)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

MEDIA_URL = 'data/'
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'reportcreator_api.conf.plugins.AppDirectoriesFinderWithoutPluginApps',
    'reportcreator_api.conf.plugins.PluginDirectoriesFinder',
]

DEFAULT_FILE_STORAGE = config('DEFAULT_FILE_STORAGE', default='filesystem')
DEFAULT_S3_ACCESS_KEY = config('DEFAULT_S3_ACCESS_KEY', default='')
DEFAULT_S3_SECRET_KEY = config('DEFAULT_S3_SECRET_KEY', default='')
DEFAULT_S3_SESSION_TOKEN = config('DEFAULT_S3_SESSION_TOKEN', default=None)
DEFAULT_S3_BUCKET_NAME = config('DEFAULT_S3_BUCKET_NAME', default='')
DEFAULT_S3_ENDPOINT_URL = config('DEFAULT_S3_ENDPOINT_URL', default='')

UPLOADED_IMAGE_STORAGE = config('UPLOADED_IMAGE_STORAGE', default=DEFAULT_FILE_STORAGE)
UPLOADED_IMAGE_STORAGE = {
    'filesystem': 'reportcreator_api.utils.storages.EncryptedFileSystemStorage',
    's3': 'reportcreator_api.utils.storages.EncryptedS3Storage',
}.get(UPLOADED_IMAGE_STORAGE, UPLOADED_IMAGE_STORAGE)

UPLOADED_ASSET_STORAGE = config('UPLOADED_ASSET_STORAGE', default=DEFAULT_FILE_STORAGE)
UPLOADED_ASSET_STORAGE = {
    'filesystem': 'reportcreator_api.utils.storages.EncryptedFileSystemStorage',
    's3': 'reportcreator_api.utils.storages.EncryptedS3Storage',
}.get(UPLOADED_ASSET_STORAGE, UPLOADED_ASSET_STORAGE)

UPLOADED_FILE_STORAGE = config('UPLOADED_FILE_STORAGE', default=DEFAULT_FILE_STORAGE)
UPLOADED_FILE_STORAGE = {
    'filesystem': 'reportcreator_api.utils.storages.EncryptedFileSystemStorage',
    's3': 'reportcreator_api.utils.storages.EncryptedS3Storage',
}.get(UPLOADED_FILE_STORAGE, UPLOADED_FILE_STORAGE)

ARCHIVED_FILE_STORAGE = config('ARCHIVED_FILE_STORAGE', default=DEFAULT_FILE_STORAGE)
ARCHIVED_FILE_STORAGE = {
    'filesystem': 'reportcreator_api.utils.storages.UnencryptedFileSystemStorage',
    's3': 'reportcreator_api.utils.storages.UnencryptedS3Storage',
}.get(ARCHIVED_FILE_STORAGE, ARCHIVED_FILE_STORAGE)

STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
    'uploaded_images': {
        'BACKEND': UPLOADED_IMAGE_STORAGE,
        'OPTIONS': {
            'location': config('UPLOADED_IMAGE_LOCATION', default=(MEDIA_ROOT if 'filesystem' in UPLOADED_IMAGE_STORAGE.lower() else Path()) / 'uploadedimages', cast=Path),
            'access_key': config('UPLOADED_IMAGE_S3_ACCESS_KEY', default=DEFAULT_S3_ACCESS_KEY),
            'secret_key': config('UPLOADED_IMAGE_S3_SECRET_KEY', default=DEFAULT_S3_SECRET_KEY),
            'security_token': config('UPLOADED_IMAGE_S3_SESSION_TOKEN', default=DEFAULT_S3_SESSION_TOKEN),
            'bucket_name': config('UPLOADED_IMAGE_S3_BUCKET_NAME', default=DEFAULT_S3_BUCKET_NAME),
            'endpoint_url': config('UPLOADED_IMAGE_S3_ENDPOINT_URL', default=DEFAULT_S3_ENDPOINT_URL),
        },
    },
    'uploaded_assets': {
        'BACKEND': UPLOADED_ASSET_STORAGE,
        'OPTIONS': {
            'location': config('UPLOADED_ASSET_LOCATION', default=(MEDIA_ROOT if 'filesystem' in UPLOADED_ASSET_STORAGE.lower() else Path()) / 'uploadedassets', cast=Path),
            'access_key': config('UPLOADED_ASSET_S3_ACCESS_KEY', default=DEFAULT_S3_ACCESS_KEY),
            'secret_key': config('UPLOADED_ASSET_S3_SECRET_KEY', default=DEFAULT_S3_SECRET_KEY),
            'security_token': config('UPLOADED_ASSET_S3_SESSION_TOKEN', default=DEFAULT_S3_SESSION_TOKEN),
            'bucket_name': config('UPLOADED_ASSET_S3_BUCKET_NAME', default=DEFAULT_S3_BUCKET_NAME),
            'endpoint_url': config('UPLOADED_ASSET_S3_ENDPOINT_URL', default=DEFAULT_S3_ENDPOINT_URL),
        },
    },
    'uploaded_files': {
        'BACKEND': UPLOADED_FILE_STORAGE,
        'OPTIONS': {
            'location': config('UPLOADED_FILE_LOCATION', default=(MEDIA_ROOT if 'filesystem' in UPLOADED_FILE_STORAGE.lower() else Path()) / 'uploadedfiles', cast=Path),
            'access_key': config('UPLOADED_FILE_S3_ACCESS_KEY', default=DEFAULT_S3_ACCESS_KEY),
            'secret_key': config('UPLOADED_FILE_S3_SECRET_KEY', default=DEFAULT_S3_SECRET_KEY),
            'security_token': config('UPLOADED_FILE_S3_SESSION_TOKEN', default=DEFAULT_S3_SESSION_TOKEN),
            'bucket_name': config('UPLOADED_FILE_S3_BUCKET_NAME', default=DEFAULT_S3_BUCKET_NAME),
            'endpoint_url': config('UPLOADED_FILE_S3_ENDPOINT_URL', default=DEFAULT_S3_ENDPOINT_URL),
        },
    },
    'archived_files': {
        'BACKEND': ARCHIVED_FILE_STORAGE,
        'OPTIONS': {
            'location': config('ARCHIVED_FILE_LOCATION', default=(MEDIA_ROOT if 'filesystem' in UPLOADED_FILE_STORAGE.lower() else Path()) / 'archivedfiles', cast=Path),
            'access_key': config('ARCHIVED_FILE_S3_ACCESS_KEY', default=DEFAULT_S3_ACCESS_KEY),
            'secret_key': config('ARCHIVED_FILE_S3_SECRET_KEY', default=DEFAULT_S3_SECRET_KEY),
            'security_token': config('ARCHIVED_FILE_S3_SESSION_TOKEN', default=DEFAULT_S3_SESSION_TOKEN),
            'bucket_name': config('ARCHIVED_FILE_S3_BUCKET_NAME', default=DEFAULT_S3_BUCKET_NAME),
            'endpoint_url': config('ARCHIVED_FILE_S3_ENDPOINT_URL', default=DEFAULT_S3_ENDPOINT_URL),
        },
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.PentestUser'


# HTTP Header settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': [NONE],
        'img-src': [SELF, 'data:'],
        'font-src': [SELF],
        'worker-src': [SELF],
        'connect-src': [SELF, 'data:'],
        'frame-src': [SELF],
        'frame-ancestors': [SELF],
        'form-action': [SELF],
        # nuxt, vuetify and markdown preview use inline styles
        'style-src': [SELF, UNSAFE_INLINE],
        # hash of nuxt inline script injected in index.html
        'script-src': [SELF, "'sha256-vfPLwqW0BNyGGLG6upxgxsXF+K7Jp/V2hJGlbPt7NJY='"],
        # Trusted types are not compatible with django admin, django rest framework's browsable API, swagger UI and django debug toolbar
        # 'require-trusted-types-for': ["'script'"],
        # 'trusted-types': [
        #     'default',  # required for vuetify, unhead, mermaid
        #     'worker-url',  # load web workers via import URL
        #     'vue',  # used by vue and markdown
        #     'dompurify',  # used by mermaid
        #     "'allow-duplicates'",  # dompurify is used twice as dependency
        #     # monaco-editor policies
        #     'defaultWorkerFactory', 'tokenizeToString', 'standaloneColorizer',
        #     'editorViewLayer', 'domLineBreaksComputer', 'domLineBreaksComputer',
        #     'diffEditorWidget', 'editorGhostText', 'diffReview', 'stickyScrollViewLayer',
        # ],
    },
}

PERMISSIONS_POLICY = {
    'publickey-credentials-get': '(self)',
    'clipboard-write': '(self)',
    'accelerometer': '()',
    'ambient-light-sensor': '()',
    'autoplay': '()',
    'battery': '()',
    'camera': '()',
    'cross-origin-isolated': '()',
    'display-capture': '()',
    'document-domain': '()',
    'encrypted-media': '()',
    'execution-while-not-rendered': '()',
    'execution-while-out-of-viewport': '()',
    'fullscreen': '()',
    'geolocation': '()',
    'gyroscope': '()',
    'keyboard-map': '()',
    'magnetometer': '()',
    'microphone': '()',
    'midi': '()',
    'navigation-override': '()',
    'payment': '()',
    'picture-in-picture': '()',
    'screen-wake-lock': '()',
    'sync-xhr': '()',
    'usb': '()',
    'web-share': '()',
    'xr-spatial-tracking': '()',
    'clipboard-read': '()',
    'gamepad': '()',
    'speaker-selection': '()',
}


# Generate HTTPS URIs in responses for requests behind a reverse proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', cast=bool, default=False)
USE_X_FORWARDED_PORT = config('USE_X_FORWARDED_PORT', cast=bool, default=False)

# SSL required
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', cast=bool, default=False)
SECURE_REDIRECT_EXEMPT = [r'^api/v1/utils/healthcheck/?$', r'^api/public/utils/healthcheck/?$']
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT


# Monkey-Patch django to disable CSRF everywhere
# CSRF middlware class is used as middleware and internally by DjangoRestFramework
from django.middleware import csrf  # noqa: E402

from reportcreator_api.utils.middleware import CustomCsrfMiddleware  # noqa: E402

csrf.CsrfViewMiddleware = CustomCsrfMiddleware


PDF_RENDER_SCRIPT_PATH = config('PDF_RENDER_SCRIPT_PATH', cast=Path, default=BASE_DIR / '..' / 'rendering' / 'dist' / 'bundle.js')
CHROMIUM_EXECUTABLE = config('CHROMIUM_EXECUTABLE', default='/usr/lib/chromium/chromium')
GHOSTSCRIPT_EXECUTABLE = config('GHOSTSCRIPT_EXECUTABLE', default='/usr/bin/gs')


# Celery client settings
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='')
CELERY_BROKER_URL_FILE = config('CELERY_BROKER_URL_FILE', default=None)
if not CELERY_BROKER_URL and CELERY_BROKER_URL_FILE:
    CELERY_BROKER_URL = Path(CELERY_BROKER_URL_FILE).read_text()
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='rpc://')


CELERY_RESULT_EXPIRES = timedelta(seconds=30)
CELERY_TASK_DEFAULT_EXCHANGE = 'tasks'
CELERY_TASK_QUEUES_NO_DECLARE = config('CELERY_TASK_QUEUES_NO_DECLARE', cast=bool, default=False)
CELERY_TASK_QUEUES = [
    Queue('rendering', routing_key='tasks.rendering', no_declare=CELERY_TASK_QUEUES_NO_DECLARE),
]
CELERY_TASK_ROUTES = {
    'reportcreator.render_pdf': {
        'exchange': CELERY_TASK_DEFAULT_EXCHANGE,
        'queue': 'rendering',
        'routing_key': 'tasks.rendering',
    },
}


# Celery worker settings
CELERY_SECURE_WORKER = config('CELERY_SECURE_WORKER', cast=bool, default=False)
if CELERY_SECURE_WORKER:
    CELERY_WORKER_POOL = 'prefork'
    CELERY_WORKER_CONCURRENCY = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_BROKER_POOL_LIMIT = 0
    CELERY_TASK_ACKS_LATE = False
    CELERY_WORKER_ENABLE_REMOTE_CONTROL = True


CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_SEND_TASK_EVENTS = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Execute tasks locally, if no broker is configured
CELERY_TASK_ALWAYS_EAGER = not CELERY_BROKER_URL

# Time limits are only enforced if a broker is configured and an external worker is used (but not in eager mode).
# Self-hosted SysReptor instances use the eager mode by default, resulting in no PDF rendering time limits being applied.
PDF_RENDERING_TIME_LIMIT = config('PDF_RENDERING_TIME_LIMIT', cast=int, default=60)


# History
class LicenseCheckBooleanProxy:
    def __bool__(self):
        from reportcreator_api.utils import license
        return license.is_professional(skip_db_checks=True)
SIMPLE_HISTORY_ENABLED = LicenseCheckBooleanProxy()
SIMPLE_HISTORY_HISTORY_ID_USE_UUID = True
SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = True
SIMPLE_HISTORY_REVERT_DISABLED = True
SIMPLE_HISTORY_CLEANUP_TIMEFRAME = timedelta(hours=2)


# Periodic tasks
PERIODIC_TASKS = [
    {
        'id': 'fetch_notifications',
        'task': 'reportcreator_api.notifications.tasks.fetch_notifications',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'clear_sessions',
        'task': 'reportcreator_api.utils.tasks.clear_sessions',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'cleanup_unreferenced_images_and_files',
        'task': 'reportcreator_api.pentests.tasks.cleanup_unreferenced_images_and_files',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'reset_stale_archive_restores',
        'task': 'reportcreator_api.pentests.tasks.reset_stale_archive_restores',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'automatically_archive_projects',
        'task': 'reportcreator_api.pentests.tasks.automatically_archive_projects',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'automatically_delete_archived_projects',
        'task': 'reportcreator_api.pentests.tasks.automatically_delete_archived_projects',
        'schedule': timedelta(days=1),
    },
    {
        'id': 'cleanup_history',
        'task': 'reportcreator_api.pentests.tasks.cleanup_history',
        'schedule': timedelta(minutes=5),
    },
    {
        'id': 'cleanup_collab_events',
        'task': 'reportcreator_api.pentests.tasks.cleanup_collab_events',
        'schedule': timedelta(hours=1),
    },
]


# MAX_LOCK_TIME should not be less than 1.30min, because some browsers (Chromium) triggers timers only once per minute if the browser tab is inactive
MAX_LOCK_TIME = timedelta(seconds=90)

SPELLCHECK_URL = config('SPELLCHECK_URL', default=None)
SPELLCHECK_DICTIONARY_PER_USER = config('SPELLCHECK_DICTIONARY_PER_USER', cast=bool, default=False)
SPELLCHECK_MODE_PICKY = config('SPELLCHECK_MODE_PICKY', cast=bool, default=False)
SPELLCHECK_LANGUAGETOOL_CONFIG = config('SPELLCHECK_LANGUAGETOOL_CONFIG', cast=json.loads, default='{"disabledRules": "TODO,TO_DO_HYPHEN"}')

BACKUP_KEY = config('BACKUP_KEY', default=None)

COMPRESS_IMAGES = config('COMPRESS_IMAGES', cast=bool, default=True)
COMPRESS_PDFS = config('COMPRESS_PDFS', cast=bool, default=True)

REGEX_VALIDATION_TIMEOUT = timedelta(milliseconds=500)


from reportcreator_api.archive.crypto import EncryptionKey  # noqa: E402

ENCRYPTION_KEYS = EncryptionKey.from_json_list(config('ENCRYPTION_KEYS', default=''))
DEFAULT_ENCRYPTION_KEY_ID = config('DEFAULT_ENCRYPTION_KEY_ID', default=None)
ENCRYPTION_PLAINTEXT_FALLBACK = config('ENCRYPTION_PLAINTEXT_FALLBACK', cast=bool, default=True)

GUEST_USERS_CAN_EDIT_PROJECTS = config('GUEST_USERS_CAN_EDIT_PROJECTS', cast=bool, default=True)
GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS = config('GUEST_USERS_CAN_UPDATE_PROJECT_SETTINGS', cast=bool, default=GUEST_USERS_CAN_EDIT_PROJECTS)
GUEST_USERS_CAN_CREATE_PROJECTS = config('GUEST_USERS_CAN_CREATE_PROJECTS', cast=bool, default=GUEST_USERS_CAN_EDIT_PROJECTS)
GUEST_USERS_CAN_DELETE_PROJECTS = config('GUEST_USERS_CAN_DELETE_PROJECTS', cast=bool, default=GUEST_USERS_CAN_EDIT_PROJECTS)
GUEST_USERS_CAN_IMPORT_PROJECTS = config('GUEST_USERS_CAN_IMPORT_PROJECTS', cast=bool, default=False)
GUEST_USERS_CAN_SEE_ALL_USERS = config('GUEST_USERS_CAN_SEE_ALL_USERS', cast=bool, default=False)
GUEST_USERS_CAN_SHARE_NOTES = config('GUEST_USERS_CAN_SHARE_NOTES', cast=bool, default=False)


DISABLE_SHARING = config('DISABLE_SHARING', cast=bool, default=False)
SHARING_PASSWORD_REQUIRED = config('SHARING_PASSWORD_REQUIRED', cast=bool, default=False)
SHARING_READONLY_REQUIRED = config('SHARING_READONLY_REQUIRED', cast=bool, default=False)


ENABLE_PRIVATE_DESIGNS = config('ENABLE_PRIVATE_DESIGNS', cast=bool, default=False)

ARCHIVING_THRESHOLD = config('ARCHIVING_THRESHOLD', cast=int, default=2)
assert ARCHIVING_THRESHOLD > 0
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER = config('AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER', cast=int, default=0)
AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER = timedelta(days=AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER) if AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER else None
AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER = config('AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER', cast=int, default=0)
AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER = timedelta(days=AUTOMATICALLY_DELETE_ARCHIVED_PROJECTS_AFTER) if AUTOMATICALLY_ARCHIVE_PROJECTS_AFTER else None
AUTOMATICALLY_RESET_STALE_ARCHIVE_RESTORES_AFTER = timedelta(days=3)


# Health checks
HEALTH_CHECKS = {
    'database': 'reportcreator_api.api_utils.healthchecks.check_database',
    'migrations': 'reportcreator_api.api_utils.healthchecks.check_migrations',
    # 'cache': 'reportcreator_api.api_utils.healthchecks.check_cache',
}

# Notifications
VERSION = config('VERSION', default='dev')
INSTANCE_TAGS = config('INSTANCE_TAGS', cast=Csv(delimiter=';'), default='on-premise')
NOTIFICATION_IMPORT_URL = config('NOTIFICATION_IMPORT_URL', default='https://cloud.sysreptor.com/api/v1/notifications/')

# License
LICENSE = config('LICENSE', default=None)
LICENSE_VALIDATION_KEYS = [
    {'id': 'amber', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAkqCS3lZbrzh+2mKTYymqPHtKBrh8glFxnj9OcoQR9xQ='},
    {'id': 'silver', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAwu/cl0CZSSBFOzFSz/hhUQQjHIKiT4RS3ekPevSKn7w='},
    {'id': 'magenta', 'algorithm': 'ed25519', 'key': 'MCowBQYDK2VwAyEAd10mgfTx0fuPO6KwcYU98RLhreCF+BQCeI6CAs0YztA='},
]
LICENSE_COMMUNITY_MAX_USERS = 3

INSTALLATION_ID_PATH = MEDIA_ROOT / 'installation_id'
if not INSTALLATION_ID_PATH.exists():
    INSTALLATION_ID_PATH.write_text(str(uuid.uuid4()))
INSTALLATION_ID = INSTALLATION_ID_PATH.read_text().strip()


# Languages
PREFERRED_LANGUAGES = config('PREFERRED_LANGUAGES', cast=Csv(), default=None)


# Plugins
PLUGIN_DIRS = [
    BASE_DIR / 'reportcreator_api' / 'plugins',
]
ENABLED_PLUGINS = [
    'demoplugin',
    'cyberchef',
]
INSTALLED_APPS += load_plugins(PLUGIN_DIRS, ENABLED_PLUGINS)


# Elastic APM
ELASTIC_APM_ENABLED = config('ELASTIC_APM_ENABLED', cast=bool, default=False)
ELASTIC_APM = {
    'ENABLED': ELASTIC_APM_ENABLED,
    'SERVICE_NAME': config('ELASTIC_APM_SERVICE_NAME', default=''),
    'API_KEY': config('ELASTIC_APM_SERVICE_TOKEN', default=''),
    'SERVER_URL': config('ELASTIC_APM_SERVER_URL', default=''),
    'SPAN_COMPRESSION_ENABLED': False,
    'DJANGO_AUTOINSERT_MIDDLEWARE': False,
    'DJANGO_TRANSACTION_NAME_FROM_ROUTE': True,
}
if ELASTIC_APM_ENABLED:
    INSTALLED_APPS.append('elasticapm.contrib.django')

ELASTIC_APM_RUM_ENABLED = config('ELASTIC_APM_RUM_ENABLED', cast=bool, default=False)
ELASTIC_APM_RUM_CONFIG = {
    'active': ELASTIC_APM_RUM_ENABLED,
    'serviceName': config('ELASTIC_APM_RUM_SERVICE_NAME', default=''),
    'serverUrl': config('ELASTIC_APM_RUM_SERVER_URL', default=''),
    'serviceVersion': 'dev',
}
if ELASTIC_APM_RUM_ENABLED:
    CONTENT_SECURITY_POLICY['DIRECTIVES']['connect-src'].append(ELASTIC_APM_RUM_CONFIG['serverUrl'])


if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INTERNAL_IPS = type('c', (), {'__contains__': lambda *a: True})()



logging_handlers = ['console'] + (['elasticapm'] if ELASTIC_APM_ENABLED else [])
LOGGING = {
    'version': 1,
    'disabled_existing_loggers': False,
    'formatters': {
        'default': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        **({
            'elasticapm': {
                'level': 'WARNING',
                'class': 'elasticapm.contrib.django.handlers.LoggingHandler',
            },
        } if ELASTIC_APM_ENABLED else {}),
    },
    'root': {
        'level': 'INFO',
        'handlers': logging_handlers,
    },
    'loggers': {
        'celery': {
            'level': 'WARNING',
            'handlers': logging_handlers,
            'propagate': False,
        },
        'celery.worker.strategy': {
            'level': 'INFO',
            'handlers': logging_handlers,
            'propagate': False,
        },
        'weasyprint': {
            'level': 'ERROR',
            'handlers': logging_handlers,
            'propagate': False,
        },
        'playwright': {
            'level': 'WARNING',
            'hanlders': logging_handlers,
            'propagate': False,
        },
        'pikepdf': {
            'level': 'WARNING',
            'handlers': logging_handlers,
            'propagate': False,
        },
        'fontTools': {
            'level': 'WARNING',
            'handlers': logging_handlers,
            'propagate': False,
        },
    },
}
