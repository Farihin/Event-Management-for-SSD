"""
Production settings — full hardening. DEBUG is OFF (custom error pages active,
no stack traces leak), and the SECURE_* matrix is set to hard values so the
security posture is auditable in one place. CSP is ENFORCED (not report-only).

Run `python manage.py check --deploy --settings=eventproject.settings.prod`
to verify this matrix.
"""

from .base import *  # noqa: F401,F403
from .base import CSRF_TRUSTED_ORIGINS, env

DEBUG = False
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")          # must be set explicitly in the prod env

# Trust the Cloudflare-tunnel public origin for CSRF (login/forms over the tunnel).
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + ["https://django.zahar.my"]

# --- Transport security (A02) ---
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # if behind a TLS proxy
SECURE_HSTS_SECONDS = 31536000                       # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Secure cookies (A02/A07) ---
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- Headers (A05) ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# CSP is enforced in production (CONTENT_SECURITY_POLICY inherited from base; no
# report-only override here).
