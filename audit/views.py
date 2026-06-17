"""
Admin-only Audit Log page  [A09].
"""

from django.views.generic import ListView

from accounts.mixins import AdminRequiredMixin

from .models import AuditLog


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "audit/auditlog_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("actor")
        # Filter inputs are validated against the allowed choices (whitelist).
        action = self.request.GET.get("action", "")
        if action in AuditLog.Action.values:
            qs = qs.filter(action=action)
        actor = self.request.GET.get("actor", "").strip()
        if actor:
            qs = qs.filter(actor__username__icontains=actor)  # parameterized by the ORM
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_choices"] = AuditLog.Action.choices
        ctx["current_action"] = self.request.GET.get("action", "")
        ctx["current_actor"] = self.request.GET.get("actor", "")
        return ctx
