"""
Account views: self-service registration and profile editing.

Login / logout / password-reset use Django's built-in auth views (wired in
urls.py). Registration always creates a Normal-User account; the profile view is
hard-scoped to request.user so a user can only ever edit their own profile
(no IDOR).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from audit.models import AuditLog
from audit.utils import log_audit_event

from .forms import ProfileForm, RegisterForm
from .models import User


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("events:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request, AuditLog.Action.REGISTER, actor=self.object,
                        message="New account registered")
        messages.success(self.request, "Account created successfully. Please log in.")
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        # Always the logged-in user — the URL carries no id, so there is nothing
        # to tamper with (IDOR-proof by construction).
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)
