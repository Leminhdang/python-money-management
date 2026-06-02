"""
Cấu hình Django cho project Quản Lý Thu Chi.
Tạo bởi django-admin startproject, Django 6.0.5.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --- Cấu hình bảo mật ---

# TODO: đổi secret key khi deploy lên production
SECRET_KEY = 'django-insecure-5@+x@u25=4_svyaxlk3vb$#-r1l5l@bk1^3a#8c!jcldz&&mcj'

DEBUG = True

ALLOWED_HOSTS = []


# --- Ứng dụng ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Thư viện bên ngoài
    'rest_framework',

    # App của project
    'users',
    'expenses',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'quan_ly_thu_chi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'quan_ly_thu_chi.wsgi.application'


# --- Database ---
# Dùng SQLite cho giai đoạn phát triển, sau này chuyển PostgreSQL nếu cần

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- Xác thực mật khẩu ---

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


# --- Ngôn ngữ và Múi giờ ---

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- File tĩnh ---

STATIC_URL = 'static/'

# Dùng model User tùy chỉnh thay cho User mặc định
AUTH_USER_MODEL = 'users.User'

# Cấu hình DRF: xác thực bằng JWT làm chính
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# Cấu hình JWT – access token sống 24h, refresh 7 ngày
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,
}
