from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only registration so the audit trail cannot be tampered with via the
    admin site."""

    list_display = ("timestamp", "action", "actor", "success", "ip_address", "target_repr")
    list_filter = ("action", "success", "timestamp")
    search_fields = ("actor__username", "message", "target_repr", "ip_address")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
