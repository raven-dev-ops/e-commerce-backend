import os
from pathlib import Path
from dotenv import load_dotenv
import warnings
from mongoengine import connect

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-...')
DEBUG = True
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.herokuapp.com').split(',')

INSTALLED_APPS = [
    # Removed default Django apps using relational DB
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    # 'django.contrib.sites',

    # Only include apps that support MongoEngine or are non-relational
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

    'users',
    'products',
    'orders',
    'cart',
    'payments',
    'discounts',
    'reviews',
    'authentication',
]

SITE_ID = 1

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

ACCOUNT_SIGNUP_FIELDS = ['username', 'email', 'password1', 'password2']
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# REMOVE default relational database setup
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Connect to MongoDB
MONGO_URI = os.getenv('MONGO_URI')
connect(
    db="website",
    host=MONGO_URI,
)

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
    raise ValueError("Stripe keys are not set in environment variables")

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

CORS_ALLOWED_ORIGINS = [
    "https://twiinz-beard-frontend.netlify.app",
    "http://localhost:3000",
]
CORS_ALLOW_CREDENTIALS = True

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
