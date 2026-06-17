"""
RBAC + ownership mixins for class-based views  [A01 / ASVS V4].
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import User


class RoleRequiredMixin(LoginRequiredMixin):
    """Require an authenticated user whose role is in ``allowed_roles``.

    Anonymous -> redirect to login (LoginRequiredMixin). Authenticated but wrong
    role -> 403.
    """

    allowed_roles: tuple = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (User.Roles.ADMIN,)


class OwnerQuerysetMixin(LoginRequiredMixin):
    """Object-level scoping that prevents IDOR.

    A non-admin only ever sees objects they own, so a guessed PK belonging to
    another user resolves to 404 (object simply not in the queryset) rather than
    exposing or 403-confirming someone else's record. Admins see everything.
    """

    owner_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, "is_admin_role", False):
            return qs
        return qs.filter(**{self.owner_field: self.request.user})
