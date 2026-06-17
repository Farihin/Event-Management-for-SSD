"""
Security tests for the events app: RBAC enforcement, IDOR resistance,
capacity / duplicate-registration controls, and XSS output encoding.
"""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Event, Registration

STRONG = "Str0ng#Passw0rd"


def make_user(username, role=User.Roles.USER):
    u = User.objects.create_user(username, f"{username}@example.com", STRONG)
    if role == User.Roles.ADMIN:
        u.role = User.Roles.ADMIN
        u.save()
    return u


def make_event(organizer, status=Event.Status.PUBLISHED, capacity=10, title="Test Event"):
    now = timezone.now()
    return Event.objects.create(
        title=title, description="A description.", location="Somewhere",
        start_at=now + timedelta(days=1), end_at=now + timedelta(days=1, hours=2),
        capacity=capacity, status=status, organizer=organizer,
    )


class RbacTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin", User.Roles.ADMIN)
        self.user = make_user("user")

    def test_normal_user_cannot_open_create(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("events:create")).status_code, 403)

    def test_admin_can_open_create(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("events:create")).status_code, 200)

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("events:create"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)


class IdorTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin", User.Roles.ADMIN)
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.event = make_event(self.admin)
        self.bob_reg = Registration.objects.create(user=self.bob, event=self.event)

    def test_user_cannot_cancel_another_users_registration(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("events:cancel", args=[self.bob_reg.pk]))
        self.assertEqual(resp.status_code, 404)
        self.bob_reg.refresh_from_db()
        self.assertEqual(self.bob_reg.status, Registration.Status.CONFIRMED)

    def test_draft_event_hidden_from_normal_user(self):
        draft = make_event(self.admin, status=Event.Status.DRAFT, title="Secret Draft")
        self.client.force_login(self.alice)
        self.assertEqual(
            self.client.get(reverse("events:detail", args=[draft.pk])).status_code, 404
        )


class RegistrationControlTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin", User.Roles.ADMIN)
        self.user = make_user("user")

    def test_duplicate_registration_blocked_via_view(self):
        event = make_event(self.admin, capacity=5)
        self.client.force_login(self.user)
        self.client.post(reverse("events:register", args=[event.pk]))
        self.client.post(reverse("events:register", args=[event.pk]))
        self.assertEqual(
            Registration.objects.filter(event=event, status="confirmed").count(), 1
        )

    def test_capacity_enforced(self):
        event = make_event(self.admin, capacity=1)
        self.client.force_login(self.user)
        self.client.post(reverse("events:register", args=[event.pk]))
        other = make_user("other")
        self.client.force_login(other)
        self.client.post(reverse("events:register", args=[event.pk]))
        self.assertEqual(
            Registration.objects.filter(event=event, status="confirmed").count(), 1
        )

    def test_unique_constraint_enforced_at_db(self):
        event = make_event(self.admin)
        Registration.objects.create(user=self.user, event=event)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Registration.objects.create(user=self.user, event=event)


class XssTests(TestCase):
    def test_description_is_escaped(self):
        admin = make_user("admin", User.Roles.ADMIN)
        event = make_event(admin, title="Safe Title")
        event.description = "<script>alert('xss')</script>"
        event.save()
        self.client.force_login(make_user("viewer"))
        resp = self.client.get(reverse("events:detail", args=[event.pk]))
        self.assertNotContains(resp, "<script>alert('xss')</script>")
        self.assertContains(resp, "&lt;script&gt;")
