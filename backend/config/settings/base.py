"""
Django settings base – shared across all environments.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")
AUTH_USER_MODEL = "users.User"
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",          # OpenAPI 3.0 schema generation (Swagger / Redoc)
    # Local
    "apps.users",
    "apps.audit",
    "apps.leads",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # Must be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database – PostgreSQL via environment variables
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Email Settings (SMTP) ───────────────────────────────────────────
# Pour utiliser Gmail:
# 1. Activez la validation en deux étapes sur votre compte Google.
# 2. Créez un "Mot de passe d'application" (App Password).
# 3. Utilisez ce mot de passe de 16 caractères ci-dessous.

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'alimekni5@gmail.com'  
EMAIL_HOST_PASSWORD = 'ddmu fdrv xwhh xbww'  
DEFAULT_FROM_EMAIL = f'crmPfe <{EMAIL_HOST_USER}>'

# Pour le développement (affiche les mails dans la console au lieu de les envoyer):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.users.exceptions.custom_exception_handler",
    # Register drf-spectacular as the schema generator
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ---------------------------------------------------------------------------
# drf-spectacular — OpenAPI 3.0 schema configuration
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "crmPfe Auth API",
    "DESCRIPTION": (
        "Authentication and user management API for the crmPfe / Qualifix platform.\n\n"
        "## Authentication\n"
        "This API uses **HTTP-only cookie-based JWT** authentication.\n\n"
        "- After a successful `POST /api/auth/login/` or `POST /api/auth/register/`, "
        "the server sets two HTTP-only cookies: `access_token` (10 min) and `refresh_token` (7 days).\n"
        "- Tokens are **never** returned in the JSON body.\n"
        "- All mutating requests must include the `X-CSRFToken` header (read from the "
        "readable `csrftoken` cookie).\n"
        "- When the access token expires, `POST /api/auth/refresh/` issues a new pair "
        "using the refresh cookie — the original request is retried transparently by Axios.\n\n"
        "## Cookie Security\n"
        "| Cookie | HttpOnly | Secure (prod) | SameSite | Purpose |\n"
        "|--------|----------|---------------|----------|---------|\n"
        "| `access_token` | ✅ Yes | ✅ Yes | Lax | Authenticates API requests |\n"
        "| `refresh_token` | ✅ Yes | ✅ Yes | Lax | Rotates session silently |\n"
        "| `csrftoken` | ❌ No | ❌ No | Lax | Read by JS for CSRF header |\n"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # Don't expose the raw /schema/ endpoint in production
    "COMPONENT_SPLIT_REQUEST": True,  # Separate request/response schemas for the same endpoint
    "SCHEMA_PATH_PREFIX": "/api/",
    # Define the cookie-based security scheme
    "SECURITY": [
        {"cookieAuth": []},
    ],
    "COMPONENTS": {
        "securitySchemes": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "access_token",
                "description": (
                    "HTTP-only JWT access token stored in the `access_token` cookie. "
                    "Set automatically by login/register/refresh endpoints. "
                    "Cannot be read by JavaScript."
                ),
            },
            "csrfToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-CSRFToken",
                "description": (
                    "CSRF token for mutating requests (POST/PUT/PATCH/DELETE). "
                    "Read from the non-HttpOnly `csrftoken` cookie by the Axios interceptor."
                ),
            },
        }
    },
    "POSTPROCESSING_HOOKS": ["drf_spectacular.hooks.postprocess_schema_enums"],
}

# ---------------------------------------------------------------------------
# SimpleJWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
}

# Cookie names
AUTH_COOKIE_ACCESS = "access_token"
AUTH_COOKIE_REFRESH = "refresh_token"
AUTH_COOKIE_SECURE = config("COOKIE_SECURE", default=False, cast=bool)
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_ACCESS_MAX_AGE = 60 * 10         # 10 minutes
AUTH_COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv(), default="http://localhost:5173")
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv(), default="http://localhost:5173,http://localhost:8000")
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False   # Axios needs to read it to send in header
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
