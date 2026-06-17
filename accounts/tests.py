"""
Security tests for the accounts app: password policy, registration role
hardening, username whitelist, and login auditing.
"""

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog

from .forms import RegisterForm
from .models import User

STRONG = "Str0ng#Passw0rd"


class PasswordPolicyTests(TestCase):
    def test_weak_password_rejected(self):
        form = RegisterForm(data={
            "username": "alice", "email": "alice@example.com",
            "password1": "password", "password2": "password",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_strong_password_accepted(self):
        form = RegisterForm(data={
            "username": "alice", "email": "alice@example.com",
            "password1": STRONG, "password2": STRONG,
        })
        self.assertTrue(form.is_valid(), form.errors)


class RegistrationHardeningTests(TestCase):
    def test_role_is_forced_to_normal_user(self):
        form = RegisterForm(data={
            "username": "alice", "email": "alice@example.com",
            "password1": STRONG, "password2": STRONG,
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, User.Roles.USER)
        self.assertFalse(user.is_staff)

    def test_invalid_username_rejected(self):
        form = RegisterForm(data={
            "username": "bad name!", "email": "x@example.com",
            "password1": STRONG, "password2": STRONG,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_duplicate_email_rejected(self):
        User.objects.create_user("bob", "dupe@example.com", STRONG)
        form = RegisterForm(data={
            "username": "carol", "email": "DUPE@example.com",
            "password1": STRONG, "password2": STRONG,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class LoginAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bob", "bob@example.com", STRONG)

    def test_failed_login_is_audited(self):
        self.client.post(reverse("accounts:login"),
                         {"username": "bob", "password": "wrong-password"})
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED).exists()
        )

    def test_successful_login_is_audited(self):
        self.client.post(reverse("accounts:login"),
                         {"username": "bob", "password": STRONG})
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.LOGIN_SUCCESS, actor=self.user
            ).exists()
        )


class RoleModelTests(TestCase):
    def test_admin_role_sets_is_staff(self):
        u = User.objects.create_user("adm", "adm@example.com", STRONG)
        u.role = User.Roles.ADMIN
        u.save()
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_admin_role)
