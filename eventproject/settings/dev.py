"""
Development settings.

We deliberately run the dev server over self-signed HTTPS (runserver_plus +
mkcert) so that Secure cookies, HSTS behaviour and CSP can be exercised exactly
as in production. DEBUG is ON so Django's technical error pages aid debugging;
the custom 400/403/404/500 pages are verified separately with prod settings.
"""

from .base import *  # noqa: F401,F403
from .base import CONTENT_SECURITY_POLICY as _BASE_CSP

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "django.zahar.my"]

# Allow CSRF (login/forms) to work when served through the Cloudflare tunnel.
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + ["https://django.zahar.my"]

# The dev server is genuinely HTTPS, so cookies are Secure, but we do NOT force
# an SSL redirect (we start directly on https) and we keep HSTS OFF so the
# browser never pins localhost to https in its cache.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 0

# Run CSP in REPORT-ONLY mode during development so an over-strict policy logs a
# violation instead of breaking the page while building. The enforced policy is
# disabled here (set to None) so dev emits ONLY the report-only header; prod
# enforces it.
CONTENT_SECURITY_POLICY = None
CONTENT_SECURITY_POLICY_REPORT_ONLY = _BASE_CSP
