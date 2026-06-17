"""
Audit signal receivers for authentication events  [A09].

user_login_failed receives a `credentials` dict that contains the submitted
PASSWORD — we deliberately read only the username from it and never log the
password.
"""

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import AuditLog
from .utils import get_client_ip, log_audit_event


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    log_audit_event(request, AuditLog.Action.LOGIN_SUCCESS, actor=user,
                    message="User logged in")


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    log_audit_event(request, AuditLog.Action.LOGOUT, actor=user,
                    message="User logged out")


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    username = (credentials or {}).get("username", "<unknown>")
    AuditLog.objects.create(
        actor=None,
        action=AuditLog.Action.LOGIN_FAILED,
        ip_address=get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:400] if request else ""),
        success=False,
        message=f"Failed login for username: {username}"[:500],
    )
