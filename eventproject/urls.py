"""
Root URL configuration.

Custom error handlers (handler400/403/404/500) are registered here — Django only
invokes them when DEBUG=False, so production users never see a stack trace
[A05 / ASVS V7]. Media is served by Django only in DEBUG; in production it must be
served by an auth-checked view / web server with X-Content-Type-Options: nosniff.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("events/", include("events.urls")),
    path("audit/", include("audit.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers (active only when DEBUG=False).
handler400 = "core.views.bad_request"
handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
