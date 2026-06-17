"""
Core views: a landing page and the custom error handlers.

The error handlers (wired in eventproject/urls.py) only take effect when
DEBUG=False, so no stack trace ever reaches a user  [A05 / ASVS V7].
"""

from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect("events:list")
    return render(request, "core/home.html")


def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # No `exception` argument by Django's handler500 contract; keep this template
    # self-contained (no DB / auth lookups) since something is already broken.
    return render(request, "errors/500.html", status=500)
