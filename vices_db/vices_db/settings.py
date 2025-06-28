# vices_db/settings.py
import os
try:
    import dj_database_url
except ImportError:
    print("Warning: dj_database_url not available. Install with: pip install dj-database-url")
    dj_database_url = None
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Load environment variables from the correct .env file
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file for local development
if not os.getenv('RAILWAY_ENVIRONMENT_NAME'):  # Use correct Railway variable
    env_path = BASE_DIR / '.env'  # Look for .env in the same directory as manage.py
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print(f"❌ .env not found at: {env_path}")

# Environment detection - use correct Railway variables
IS_PRODUCTION = (
    os.getenv('DJANGO_ENVIRONMENT') == 'production' or 
    os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None or
    os.getenv('RAILWAY_PROJECT_ID') is not None
)

# Security Settings
DEBUG = os.getenv('DEBUG', 'True' if not IS_PRODUCTION else 'False').lower() == 'true'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'vices-app.up.railway.app']  # Default to localhost for local development

# Generate a new secret key for production
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key-only'  # Allow dev key in debug mode
    else:
        raise ValueError("SECRET_KEY environment variable must be set in production")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_extensions',
    'users',
    'tracking',
    'goals',
    'products',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

CSRF_TRUSTED_ORIGINS = ['https://vices-app.up.railway.app']
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Move this up (right after SecurityMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vices_db.urls'

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

WSGI_APPLICATION = 'vices_db.wsgi.application'

# Database configuration
# Temporarily use SQLite locally due to driver issues
POSTGRES_LOCALLY = False  # Temporarily set to False

if ((os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('RAILWAY_PROJECT_ID')) and dj_database_url and os.getenv('DATABASE_URL')) or POSTGRES_LOCALLY:
    if POSTGRES_LOCALLY and dj_database_url and os.getenv('DATABASE_URL'):
        # Use PostgreSQL locally if POSTGRES_LOCALLY=True and DATABASE_URL is set
        DATABASES = {
            'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
        }
        print("🐘 Using PostgreSQL database (Local with POSTGRES_LOCALLY=True)")
    elif os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('RAILWAY_PROJECT_ID'):
        # Use PostgreSQL on Railway
        DATABASES = {
            'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
        }
        print("🐘 Using PostgreSQL database (Railway)")
    else:
        # Fallback to SQLite if POSTGRES_LOCALLY=True but no DATABASE_URL
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        print("🗃️ Using SQLite database (POSTGRES_LOCALLY=True but no DATABASE_URL)")
else:
    # Always use SQLite for local development by default
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("🗃️ Using SQLite database (Local Development)")

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
if cors_origins:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
else:
    # Fallback for development
    CORS_ALLOWED_ORIGINS = [
        'https://vices-app.com',
        'https://www.vices-app.com'
    ]

CORS_ALLOW_CREDENTIALS = True
STATICFILES_DIRS = []

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('DEFAULT_FROM_EMAIL', 'your-email@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'your-email@gmail.com')

# Django Allauth settings
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Cache configuration (fallback to dummy cache if Redis not available)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Security settings (only in production)
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# OpenAI API Key (optional)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
