"""
RBAC decorators for function-based views  [A01 / ASVS V4].

Wrong role -> 403 (PermissionDenied), NOT a redirect — leaking "this URL exists,
log in to reach it" is itself an access-control weakness. Anonymous users are
redirected to login by @login_required.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_required(view_func):
    """Allow only Administrator-role users."""
    return role_required(User.Roles.ADMIN)(view_func)
