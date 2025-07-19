import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import warnings
from mongoengine import connect

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-...')
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.herokuapp.com').split(',')

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.instagram',

    'django_mongoengine',
    'django_mongoengine.mongo_admin',

    # Local apps
    'users',
    'products',
    'orders',
    'cart',
    'payments',
    'discounts',
    'reviews',
    'authentication',
]

SITE_ID = 2

AUTHENTICATION_BACKENDS = [
    'authentication.backends.MongoEngineBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        }
    },
    'facebook': {
        'APP': {
            'client_id': os.getenv('FACEBOOK_APP_ID', ''),
            'secret': os.getenv('FACEBOOK_APP_SECRET', ''),
            'key': ''
        }
    },
    'instagram': {
        'APP': {
            'client_id': os.getenv('INSTAGRAM_APP_ID', ''),
            'secret': os.getenv('INSTAGRAM_APP_SECRET', ''),
            'key': ''
        }
    }
}

# Allauth / dj-rest-auth config
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_SIGNUP_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True

ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

MONGO_URI = os.getenv('MONGO_URI')
MONGODB_DATABASES = {
    "default": {
        "name": "website",
        "host": MONGO_URI,
    }
}

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
    raise ValueError("Stripe keys are not set in environment variables")

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOWED_ORIGINS = [
    "https://twiinz-beard-frontend.netlify.app",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://twiinz-beard-frontend.netlify.app",
    "https://twiinz-beard-backend-11dfd7158830.herokuapp.com",
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'products.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'mongoengine': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

REST_USE_JWT = True
REST_AUTH_TOKEN_MODEL = None

warnings.filterwarnings('ignore', message="app_settings.USERNAME_REQUIRED is deprecated")
warnings.filterwarnings('ignore', message="app_settings.EMAIL_REQUIRED is deprecated")
