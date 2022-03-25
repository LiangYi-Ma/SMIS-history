"""
Django settings for SMIS project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@%8zze-s95jxg(+5qgz830zamluh6crvlg4!wptuov$9roq^)a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'corsheaders',
    'user',
    'cv',
    'enterprise',
    'cert',
    # 评论模块
    # 'django_comments',
    # 标签模块
    'taggit',
    'django_crontab',
]

SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middleware.theMiddleWare',
    'cv.middleware.theMiddleWare',
    'enterprise.middleware.theMiddleWare',
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
#
# CORS_ORIGIN_WHITELIST = (
#     'http://127.0.0.1:8081',
#     'http://localhost:8081',
# )
#
# CORS_ALLOW_CREDENTIALS = True
#
# CORS_ORIGIN_ALLOW_ALL = True
#
# CORS_ALLOW_METHODS = (
#     'DELETE',
#     'GET',
#     'OPTIONS',
#     'PATCH',
#     'POST',
#     'PUT',
#     'VIEW',
# )
#
# CORS_ALLOW_HEADERS = (
#     'authorization',
#     'content-type',
# )

ROOT_URLCONF = 'SMIS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR), 'static'],
        # 'DIRS': ['frontend/dist'],
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

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'frontend/dist/static'),
    #    "/Users/yaqi meng/fsdownload/SMIS/static/",
)
#
# MEDIA_ROOT = "media/"
# MEDIA_URL = "media/"
# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, 'static'),
#     "/Users/yaqi meng/fsdownload/SMIS/static/",
# )
# AUTHENTICATION_BACKENDS = [
#     # Needed to login by username in Django admin, regardless of `allauth`
#     'django.contrib.auth.backends.ModelBackend',
#
#     # `allauth` specific authentication methods, such as login by e-mail
#     'allauth.account.auth_backends.AuthenticationBackend',
# ]

WSGI_APPLICATION = 'SMIS.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_smis',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
    },
    'db_cert': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_smis_for_cert',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
    }
}

DATABASE_APPS_MAPPING = {
    # example:
    # 'app_name':'database_name',
    'user': 'default',
    'cv': 'default',
    'enterprise': 'default',
    'cert': 'db_cert',
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

USE_TZ = False
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

# USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# STATIC_ROOT = '/Users/yaqi meng/fsdownload/SMIS/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# STATIC_ROOT = '/home/virtualenv/django/lib/python3.7/site-packages/django/contrib/admin/static/'

# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, 'static/'),
# )
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
#     '/Users/yaqi meng/fsdownload/SMIS/static/',
# ]
# STATICFILES_DIRS = [
#    os.path.join(BASE_DIR,'SMIS/static').replace('\\','/'),
##    os.path.join(BASE_DIR,  'static'),
##    os.path.join(BASE_DIR, 'user', 'static'),
##    os.path.join(BASE_DIR, 'cv', 'static'),
#    ]

LOGIN_URL = '/login/'

"""wx"""
AppID = 'wx9413d422ab2c7067'
AppSecret = '753a8580aaae1cbbe5da275a37ed19ba'

code2Session = 'https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'
# # 设置django—redis缓存 需要你下载插件pip install django-redis
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379',
#         'OPTIONS': {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "PASSWORD": "123456",
#         }
#     }
# }
# # 2.操作cache模块直接操作缓存：views.py
# from django.core.cache import cache  # 结合配置文件实现插拔式
# # 存放token，可以直接设置过期时间
# cache.set('token', 'header.payload.signature', 10)
# # 取出token
# token = cache.get('token')

'''邮箱设置'''
# 设置邮件域名
EMAIL_HOST = 'smtp.163.com'
# 设置端口号，为数字
EMAIL_PORT = 25
# 设置发件人邮箱
EMAIL_HOST_USER = '@163.com'
# 设置发件人 授权码
EMAIL_HOST_PASSWORD = 'pw'
# 设置是否启用安全链接
EMAIL_USER_TLS = True


'''定时任务设置'''
# 每天12点开始更新班级里的学习时长
CRONJOBS = [
    ('28 17 * * *', 'cert.api_crontab.update_online_study_progress'),
]
