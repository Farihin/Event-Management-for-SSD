"""
Event Registration views.

Access-control model:
- Event management (create/update/delete) is Admin-only (AdminRequiredMixin -> 403).
- Browsing shows only PUBLISHED events to non-admins; drafts are invisible even
  by direct UUID (404).
- Registrations are hard-scoped to request.user, so a user can never view or
  cancel someone else's registration (no IDOR).
All state-changing actions are POST-only and CSRF-protected.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from accounts.mixins import AdminRequiredMixin
from audit.mixins import AuditCreateMixin, AuditDeleteMixin, AuditUpdateMixin
from audit.models import AuditLog
from audit.utils import log_audit_event

from .forms import EventForm
from .models import Event, Registration


class EventListView(ListView):
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 9

    def get_queryset(self):
        qs = Event.objects.all()
        user = self.request.user
        if not (user.is_authenticated and user.is_admin_role):
            qs = qs.filter(status=Event.Status.PUBLISHED)
        return qs


class EventDetailView(DetailView):
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        # Non-admins can only resolve PUBLISHED events; a draft UUID 404s.
        qs = Event.objects.all()
        user = self.request.user
        if not (user.is_authenticated and user.is_admin_role):
            qs = qs.filter(status=Event.Status.PUBLISHED)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            ctx["user_registration"] = self.object.registrations.filter(
                user=user, status=Registration.Status.CONFIRMED
            ).first()
        return ctx


class EventCreateView(AdminRequiredMixin, AuditCreateMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def form_valid(self, form):
        form.instance.organizer = self.request.user  # set server-side, never from client
        messages.success(self.request, "Event created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("events:detail", kwargs={"pk": self.object.pk})


class EventUpdateView(AdminRequiredMixin, AuditUpdateMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Event updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("events:detail", kwargs={"pk": self.object.pk})


class EventDeleteView(AdminRequiredMixin, AuditDeleteMixin, DeleteView):
    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy("events:list")

    def form_valid(self, form):
        messages.success(self.request, "Event deleted.")
        return super().form_valid(form)


class RegisterForEventView(LoginRequiredMixin, View):
    """POST-only: register the current user for a published event."""

    def post(self, request, pk):
        try:
            with transaction.atomic():
                # select_for_update locks the row on PostgreSQL/MySQL (no-op on
                # SQLite); the unique constraint is the authoritative duplicate guard.
                event = get_object_or_404(
                    Event.objects.select_for_update(),
                    pk=pk,
                    status=Event.Status.PUBLISHED,
                )
                if event.is_full:
                    messages.error(request, "Sorry, this event is full.")
                    return redirect("events:detail", pk=pk)
                Registration.objects.create(
                    user=request.user, event=event,
                    status=Registration.Status.CONFIRMED,
                )
        except IntegrityError:
            messages.info(request, "You are already registered for this event.")
            return redirect("events:detail", pk=pk)

        log_audit_event(request, AuditLog.Action.CREATE, target=event,
                        message="Registered for event")
        messages.success(request, "You are now registered for this event.")
        return redirect("events:detail", pk=pk)


class MyRegistrationsListView(LoginRequiredMixin, ListView):
    template_name = "events/registration_list.html"
    context_object_name = "registrations"
    paginate_by = 10

    def get_queryset(self):
        return (
            Registration.objects.filter(user=self.request.user)
            .select_related("event")
            .order_by("-created_at")
        )


class CancelRegistrationView(LoginRequiredMixin, View):
    """POST-only: cancel one of the current user's own registrations."""

    def post(self, request, pk):
        # Ownership is baked into the queryset -> another user's registration is
        # simply not found (404), never exposed.  [IDOR / A01]
        registration = get_object_or_404(
            Registration.objects.filter(user=request.user), pk=pk
        )
        registration.status = Registration.Status.CANCELLED
        registration.save(update_fields=["status"])
        log_audit_event(request, AuditLog.Action.UPDATE, target=registration,
                        message="Cancelled registration")
        messages.success(request, "Registration cancelled.")
        return redirect("events:my_registrations")
