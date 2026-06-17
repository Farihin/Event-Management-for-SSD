"""Test-only URLconf used to exercise the custom 500 handler (a view that raises)."""

from django.urls import path


def boom(request):
    raise RuntimeError("intentional error to exercise handler500")


urlpatterns = [
    path("boom/", boom),
]

handler400 = "core.views.bad_request"
handler403 = "core.views.permission_denied"
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
