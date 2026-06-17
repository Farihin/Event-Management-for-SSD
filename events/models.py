"""
Event Registration domain.

UUID primary keys are used on objects exposed in URLs so record counts aren't
leaked and ids aren't enumerable. UUIDs are NOT access control on their own —
every view still scopes its queryset by the requesting user (see views.py).
[A01 / ASVS V4]
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.validators import IMAGE_UPLOAD_VALIDATORS, UUIDUploadTo

from .validators import title_validator


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, validators=[title_validator])
    description = models.TextField(max_length=5000)
    location = models.CharField(max_length=255)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )
    banner = models.ImageField(
        upload_to=UUIDUploadTo("event_banners"),
        validators=IMAGE_UPLOAD_VALIDATORS,
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [models.Index(fields=["status", "start_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="event_end_after_start",
            ),
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="event_capacity_positive",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            errors["end_at"] = "End time must be after the start time."
        if self.start_at and self.start_at < timezone.now():
            errors["start_at"] = "Start time cannot be in the past."
        if errors:
            raise ValidationError(errors)

    @property
    def confirmed_count(self):
        return self.registrations.filter(status=Registration.Status.CONFIRMED).count()

    @property
    def seats_available(self):
        return max(self.capacity - self.confirmed_count, 0)

    @property
    def is_full(self):
        return self.confirmed_count >= self.capacity

    def __str__(self):
        return self.title


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations"
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Race-proof duplicate prevention: only one CONFIRMED row per
            # (user, event). The partial condition still allows re-registering
            # after a cancellation.
            models.UniqueConstraint(
                fields=["user", "event"],
                condition=models.Q(status="confirmed"),
                name="uniq_active_registration_per_user_event",
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.event}"
