"""
Seed demo data so the app can be demonstrated immediately:
  - one Administrator account
  - one Normal-User account
  - a handful of published sample events

Run:  python manage.py seed
Idempotent: re-running won't create duplicates.

Demo credentials (change before any real deployment):
  admin / Admin#Secure123      (role = Administrator)
  user  / User#Secure123       (role = Normal User)
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from events.models import Event

DEMO_EVENTS = [
    ("Tech Conference 2026", "A full-day conference on secure software development.",
     "Kuala Lumpur Convention Centre", 100, 7),
    ("Django Security Workshop", "Hands-on workshop covering OWASP Top 10 in Django.",
     "Online", 30, 14),
    ("Cloud & DevSecOps Meetup", "Monthly meetup for cloud security practitioners.",
     "Cyberjaya Tech Hub", 50, 21),
    ("Intro to Threat Modeling", "Learn STRIDE and practical threat modeling.",
     "Penang Digital Library", 25, 28),
    ("Capture The Flag Night", "Beginner-friendly CTF competition with prizes.",
     "UTM Skudai", 60, 35),
]


class Command(BaseCommand):
    help = "Seed demo users and events."

    def handle(self, *args, **options):
        admin = self._ensure_user("admin", "admin@eventreg.local", "Admin#Secure123",
                                  User.Roles.ADMIN, superuser=True)
        self._ensure_user("user", "user@eventreg.local", "User#Secure123",
                          User.Roles.USER)

        now = timezone.now()
        created = 0
        for title, desc, location, capacity, days in DEMO_EVENTS:
            obj, was_created = Event.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc,
                    "location": location,
                    "capacity": capacity,
                    "start_at": now + timedelta(days=days, hours=9),
                    "end_at": now + timedelta(days=days, hours=17),
                    "status": Event.Status.PUBLISHED,
                    "organizer": admin,
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Events created this run: {created}. "
            f"Logins: admin/Admin#Secure123, user/User#Secure123"
        ))

    def _ensure_user(self, username, email, password, role, superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "role": role},
        )
        if created:
            user.role = role
            user.is_superuser = superuser
            user.is_staff = superuser or role == User.Roles.ADMIN
            user.set_password(password)
            user.save()
            self.stdout.write(f"Created {role} user: {username}")
        return user
