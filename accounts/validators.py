"""
Input-validation helpers for the accounts app  [A03 / ASVS V5].

- ComplexityValidator is wired into AUTH_PASSWORD_VALIDATORS (strong password
  rules, ASVS V2).
- USERNAME_VALIDATOR is a whitelist regex used by the registration form.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Whitelist: letters, digits and . _ - only, 3-30 chars. Anything else is rejected.
USERNAME_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9_.-]{3,30}$",
    message="Username may contain letters, numbers, and . _ - only (3-30 characters).",
)

# Reject control characters and angle brackets in free-text name fields.
NO_CONTROL_CHARS = re.compile(r"[\x00-\x1f<>]")


class ComplexityValidator:
    """Require upper, lower, digit and special characters in a password.

    Length is enforced separately by Django's MinimumLengthValidator (>= 12).
    """

    SPECIAL = r"[!@#$%^&*(),.?\":{}|<>_\-\[\]/\\;'`~+=]"

    def validate(self, password, user=None):
        missing = []
        if not re.search(r"[A-Z]", password):
            missing.append("an uppercase letter")
        if not re.search(r"[a-z]", password):
            missing.append("a lowercase letter")
        if not re.search(r"\d", password):
            missing.append("a digit")
        if not re.search(self.SPECIAL, password):
            missing.append("a special character")
        if missing:
            raise ValidationError(
                "Password must contain " + ", ".join(missing) + ".",
                code="password_too_weak",
            )

    def get_help_text(self):
        return (
            "Your password must contain at least one uppercase letter, one "
            "lowercase letter, one digit, and one special character."
        )
