"""
Authentication & profile forms with server-side input validation
[A03 / ASVS V5]. Client-side HTML5 hints are UX only and never trusted.

Privilege-escalation guard: no user-facing form ever exposes `role`, `is_staff`
or `is_superuser`. New accounts are forced to the Normal-User role in code;
role changes happen only through the Django admin.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User
from .validators import NO_CONTROL_CHARS, USERNAME_VALIDATOR


def _bootstrapify(fields):
    """Add Bootstrap classes to widgets (presentation only)."""
    for field in fields.values():
        widget = field.widget
        css = "form-control"
        if widget.__class__.__name__ in ("CheckboxInput",):
            css = "form-check-input"
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = (existing + " " + css).strip()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")   # explicit allowlist; never "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stricter whitelist on top of Django's default username validator.
        self.fields["username"].validators.append(USERNAME_VALIDATOR)
        self.fields["username"].help_text = (
            "3-30 characters: letters, numbers, and . _ - only."
        )
        _bootstrapify(self.fields)

    def clean_email(self):
        # Normalize case and enforce uniqueness (also blunts user enumeration).
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.USER          # force role server-side
        if commit:
            user.save()
        return user


class SecureAuthenticationForm(AuthenticationForm):
    """Generic failure message so the form does not reveal which field was wrong
    (anti user-enumeration)."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Invalid username or password.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "avatar")  # role NOT editable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)

    def clean_first_name(self):
        return self._clean_name(self.cleaned_data.get("first_name", ""))

    def clean_last_name(self):
        return self._clean_name(self.cleaned_data.get("last_name", ""))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("That email is already in use.")
        return email

    @staticmethod
    def _clean_name(value):
        if NO_CONTROL_CHARS.search(value):
            raise forms.ValidationError("Invalid characters in name.")
        return value.strip()
