"""
Custom user model — the single source of truth for application RBAC.

Set as AUTH_USER_MODEL = "accounts.User" BEFORE the first migrate. We subclass
AbstractUser (keeping username + password + admin integration) and add a `role`
field with exactly two values: Administrator and Normal User.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.validators import IMAGE_UPLOAD_VALIDATORS, UUIDUploadTo


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        USER = "USER", "Normal User"

    # Application role. RBAC checks (accounts.decorators / accounts.mixins) read
    # this exclusively. Whitelisted to the two values above.  [A01 / ASVS V4]
    role = models.CharField(
        max_length=5,
        choices=Roles.choices,
        default=Roles.USER,
        help_text="Application role. Controls access across the whole app.",
    )

    # Email is a required, unique credential (also used by password reset).
    email = models.EmailField("email address", unique=True)

    # Optional profile avatar uploaded by the user (File Upload Security pipeline).
    avatar = models.ImageField(
        upload_to=UUIDUploadTo("avatars"),
        validators=IMAGE_UPLOAD_VALIDATORS,
        blank=True,
        null=True,
    )

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Roles.ADMIN

    @property
    def is_normal_user(self) -> bool:
        return self.role == self.Roles.USER

    def save(self, *args, **kwargs):
        # Keep Django-admin-site access aligned with the app role, but NEVER
        # auto-grant superuser. Admins of the app can reach /admin/; normal
        # users cannot.
        if self.role == self.Roles.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
