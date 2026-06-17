"""
Audit helper — the single entry point every part of the app uses to record a
security/business event. Callers must never pass secrets; the helper only ever
writes the explicit fields below (no request bodies, cookies or headers).
[A09 / ASVS V7]
"""

import logging

from .models import AuditLog

audit_logger = logging.getLogger("audit")

# Documented denylist of keys that must never be logged anywhere.
SENSITIVE_KEYS = {
    "password", "password1", "password2", "token", "csrfmiddlewaretoken",
    "secret", "authorization", "api_key", "apikey", "ssn",
}


def get_client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit_event(request, action, *, actor=None, target=None, success=True, message=""):
    """Write one AuditLog row and mirror a non-sensitive line to the text log."""
    target_repr = target_model = target_id = ""
    if target is not None:
        target_repr = str(target)[:255]
        target_model = f"{target._meta.app_label}.{target._meta.model_name}"
        target_id = str(getattr(target, "pk", ""))

    if actor is None and request is not None:
        actor = getattr(request, "user", None)
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None

    entry = AuditLog.objects.create(
        actor=actor,
        action=action,
        target_repr=target_repr,
        target_model=target_model,
        target_id=target_id,
        ip_address=get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:400] if request else ""),
        success=success,
        message=message[:500],
    )
    audit_logger.info(
        "action=%s actor=%s target=%s success=%s ip=%s",
        action, actor, target_repr, success, entry.ip_address,
    )
    return entry
