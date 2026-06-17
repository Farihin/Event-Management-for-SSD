"""
Base settings shared by all environments for the Secure Event Registration app.

Security posture is split across three modules:
    base.py  - shared config; secrets & host-specific values read from .env
    dev.py   - local development (DEBUG=True, local HTTPS, CSP report-only)
    prod.py  - production hardening (DEBUG=False, full SECURE_* matrix, CSP enforced)

The active module is chosen by DJANGO_SETTINGS_MODULE (defaults to .dev in
manage.py / wsgi.py / asgi.py).

OWASP references are noted inline next to the control they implement
(A01..A10 = OWASP Top 10 2021; Vx = OWASP ASVS chapter).
"""

from pathlib import Path
from datetime import timedelta

import environ

# ---------------------------------------------------------------------------
# Paths & environment
# ---------------------------------------------------------------------------
# settings/base.py -> settings/ -> eventproject/ -> <project root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),                      # safe default: OFF
    DJANGO_ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    DJANGO_SECURE_SSL_REDIRECT=(bool, False),
    DJANGO_SESSION_COOKIE_SECURE=(bool, True),
    DJANGO_CSRF_COOKIE_SECURE=(bool, True),
    DJANGO_HSTS_SECONDS=(int, 0),
)
# Load .env from the project root (Configuration Security: secrets live in .env,
# never in source control).
environ.Env.read_env(BASE_DIR / ".env")

# SECURITY: no default -> a missing key raises ImproperlyConfigured (fail loud).  [A02/A05]
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")         # Host header validation  [A05]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party security stack
    "axes",                 # brute-force lockout + login attempt logging  [A07]
    "csp",                  # Content-Security-Policy headers (django-csp v4)  [A03/A05]
    "django_extensions",    # runserver_plus (local HTTPS dev/demo server)
    # local apps
    "core",                 # base templates + custom error pages
    "audit",                # audit log subsystem  [A09]
    "accounts",             # custom user, RBAC, auth
    "events",               # Event Registration CRUD
]

# Middleware order matters. SecurityMiddleware first (owns HSTS/SSL/nosniff);
# CSPMiddleware after the standard stack so request.csp_nonce is available to
# templates; AxesMiddleware MUST be last (per django-axes docs).
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves static files (incl. on the custom error pages) when DEBUG=False.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",            # CSRF protection  [A01]
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "axes.middleware.AxesMiddleware",                       # MUST be last
]

ROOT_URLCONF = "eventproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,                       # template auto-escaping is ON by default  [A03]
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",   # needed for request.csp_nonce
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eventproject.wsgi.application"
ASGI_APPLICATION = "eventproject.asgi.application"

# ---------------------------------------------------------------------------
# Database  (SQLite — the chosen DB for this project; no external server needed)
# SQL-injection safety comes from the Django ORM / parameterized queries.  [A03]
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

# ---------------------------------------------------------------------------
# Authentication, RBAC, password security
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"           # custom user is the RBAC source of truth

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "events:list"
LOGOUT_REDIRECT_URL = "accounts:login"

# django-axes: AxesStandaloneBackend MUST be first so locked-out users are blocked
# before credentials are checked.  [A07]
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Argon2id first (OWASP-preferred); the rest stay listed so legacy hashes can be
# verified and transparently upgraded.  [A02 / ASVS V2]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# Strong password rules (length >= 12 + complexity + common/numeric checks).  [ASVS V2]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "accounts.validators.ComplexityValidator"},
]

# ---------------------------------------------------------------------------
# Sessions & cookies  [A02/A07 / ASVS V3]
# ---------------------------------------------------------------------------
SESSION_COOKIE_AGE = 900                     # 15-minute lifetime
SESSION_SAVE_EVERY_REQUEST = True            # sliding idle timeout (reset on activity)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True       # no persistent session cookie
SESSION_COOKIE_HTTPONLY = True               # JS cannot read the session cookie  [XSS]
SESSION_COOKIE_SAMESITE = "Lax"              # CSRF defense-in-depth
SESSION_COOKIE_SECURE = env("DJANGO_SESSION_COOKIE_SECURE")   # HTTPS-only cookie

CSRF_COOKIE_HTTPONLY = False                 # token is rendered into forms via {% csrf_token %}
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env("DJANGO_CSRF_COOKIE_SECURE")
CSRF_TRUSTED_ORIGINS = [
    "https://localhost:8000",
    "https://127.0.0.1:8000",
]

# ---------------------------------------------------------------------------
# Security headers (shared; SSL/HSTS toggled per environment)  [A02/A05]
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"                                     # clickjacking
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = env("DJANGO_HSTS_SECONDS")

# ---------------------------------------------------------------------------
# django-axes (brute-force lockout)  [A07]
# ---------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5                                # lock after 5 failed attempts
AXES_COOLOFF_TIME = timedelta(minutes=30)            # auto-unlock after 30 minutes
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]   # lock the (IP, username) pair
AXES_RESET_ON_SUCCESS = True                         # clear counter on a good login
AXES_ENABLE_ACCESS_FAILURE_LOG = True                # persist every failure (audit trail)
AXES_LOCKOUT_TEMPLATE = "accounts/lockout.html"
AXES_VERBOSE = True

# ---------------------------------------------------------------------------
# Content-Security-Policy (django-csp v4)  [A03 defense-in-depth]
# ---------------------------------------------------------------------------
from csp.constants import SELF, NONE, NONCE  # noqa: E402

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        # Bootstrap & app JS/CSS are served from our own static/ (= SELF). NONCE
        # permits the few unavoidable inline <script>/<style> blocks per request.
        "script-src": [SELF, NONCE],
        "style-src": [SELF, NONCE],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "connect-src": [SELF],
        "frame-ancestors": [NONE],     # clickjacking (complements X-Frame-Options)
        "form-action": [SELF],         # forms may only post back to our origin
        "base-uri": [SELF],
        "object-src": [NONE],          # block plugins
    },
}

# ---------------------------------------------------------------------------
# File uploads  [File Upload Security]
# ---------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024        # 2 MB spill-to-disk threshold
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024        # max non-file request body
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100                  # form-bomb protection
FILE_UPLOAD_PERMISSIONS = 0o644
# Uploads are stored OUTSIDE the static root and are not directly executable.
MEDIA_ROOT = BASE_DIR / "private_media"
MEDIA_URL = "/media/"

# ---------------------------------------------------------------------------
# Email (dev uses the console backend; password-reset links print to the terminal)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND",
                    default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="no-reply@eventreg.local")
PASSWORD_RESET_TIMEOUT = 900                          # reset token valid 15 minutes

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kuala_Lumpur"   # GMT+8; USE_TZ keeps storage in UTC, display in this zone
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise compresses and serves static files under DEBUG=False so the custom
# error pages (and the whole site) stay styled in production.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Map the messages framework ERROR level to Bootstrap's "danger" alert class.
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: "danger"}

# ---------------------------------------------------------------------------
# Logging & monitoring  [A09 / ASVS V7]
# Two layers: the audit.AuditLog DB model (queryable security events + admin page)
# and these rotating text logs (operational/forensic). Neither stores secrets.
# ---------------------------------------------------------------------------
LOGS_DIR = BASE_DIR / "logs"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "security.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "audit.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security": {"handlers": ["security_file", "console"],
                            "level": "WARNING", "propagate": False},
        "axes": {"handlers": ["security_file", "console"],
                 "level": "INFO", "propagate": False},
        "audit": {"handlers": ["audit_file", "console"],
                  "level": "INFO", "propagate": False},
    },
}
