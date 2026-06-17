"""
Reusable CBV mixins that record CRUD actions to the audit log, keeping audit
calls out of the business logic of the events views.
"""

from .models import AuditLog
from .utils import log_audit_event


class AuditCreateMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request, AuditLog.Action.CREATE,
                        target=self.object, message="Created")
        return response


class AuditUpdateMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request, AuditLog.Action.UPDATE,
                        target=self.object, message="Updated")
        return response


class AuditDeleteMixin:
    def form_valid(self, form):
        # Log before deletion so the target's pk/repr are still available.
        log_audit_event(self.request, AuditLog.Action.DELETE,
                        target=self.object, message="Deleted")
        return super().form_valid(form)
