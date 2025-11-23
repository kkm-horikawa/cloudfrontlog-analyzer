"""
configプロジェクトのDjango設定

Django 5.2.8を使用して'django-admin startproject'により生成

このファイルの詳細については以下を参照:
https://docs.djangoproject.com/en/5.2/topics/settings/

設定の完全なリストと値については以下を参照:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path


# プロジェクト内のパスをこのように構築: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent


# クイックスタート開発設定 - 本番環境には不適切
# 参照: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# セキュリティ警告: 本番環境で使用するシークレットキーは秘密に保つこと!
SECRET_KEY = "django-insecure-#8^0ja*4ysi6bna^0+%2j07@8@7t!s+6bbvm8pq^@ti__(um1^"

# セキュリティ警告: 本番環境でDEBUGをオンにして実行しないこと!
DEBUG = True

ALLOWED_HOSTS = []


# アプリケーション定義

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# データベース
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# パスワードバリデーション
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# 国際化
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True

# CORS設定
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite開発サーバー
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# REST Framework設定
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular設定
SPECTACULAR_SETTINGS = {
    "TITLE": "CloudFront Analyzer API",
    "DESCRIPTION": "API for analyzing CloudFront access logs and detecting suspicious activities",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}


# 静的ファイル (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# デフォルトのプライマリキーフィールドタイプ
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# テスト設定
# pytestを使用するカスタムテストランナー
# これにより、python manage.py test でもpytestが実行される
TEST_RUNNER = "config.test_runner.PytestTestRunner"
