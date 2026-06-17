"""
Audit log model — queryable security/business events surfaced on an admin-only
page  [A09 / ASVS V7]. Never stores passwords, tokens or other secrets.
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login success"
        LOGIN_FAILED = "login_failed", "Login failed"
        LOGOUT = "logout", "Logout"
        LOCKOUT = "lockout", "Account locked (axes)"
        REGISTER = "register", "Account registered"
        CREATE = "create", "Object created"
        UPDATE = "update", "Object updated"
        DELETE = "delete", "Object deleted"
        PERMISSION_DENIED = "perm_denied", "Permission denied"
        SUSPICIOUS = "suspicious", "Suspicious activity"

    # Nullable: failed logins / anonymous actions have no authenticated user.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    target_repr = models.CharField(max_length=255, blank=True)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["actor", "timestamp"]),
        ]

    def __str__(self):
        who = self.actor or "anonymous"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {who} {self.action}"
