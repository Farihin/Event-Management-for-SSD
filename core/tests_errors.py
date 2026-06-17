"""
Error Handling (OWASP ASVS V7) tests:
- every custom handler returns the right status and renders its template
- under DEBUG=False, 403/404/500 serve the custom pages with NO stack trace
"""

from django.test import Client, RequestFactory, TestCase, override_settings

from accounts.models import User
from core import views as core_views

STRONG = "Str0ng#Passw0rd"


class ErrorHandlerUnitTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_each_handler_status_and_renders(self):
        req = self.rf.get("/x")
        self.assertEqual(core_views.bad_request(req, Exception()).status_code, 400)
        self.assertEqual(core_views.permission_denied(req, Exception()).status_code, 403)
        self.assertEqual(core_views.page_not_found(req, Exception()).status_code, 404)
        self.assertEqual(core_views.server_error(req).status_code, 500)


@override_settings(DEBUG=False)
class Custom404Tests(TestCase):
    def test_404_custom_page_no_traceback(self):
        resp = self.client.get("/no-such-path-xyz/")
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, "errors/404.html")
        self.assertNotIn(b"Traceback", resp.content)


@override_settings(DEBUG=False)
class Custom403Tests(TestCase):
    def test_403_custom_page_no_traceback(self):
        user = User.objects.create_user("plainuser", "plain@example.com", STRONG)
        self.client.force_login(user)
        resp = self.client.get("/events/create/")
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, "errors/403.html")
        self.assertNotIn(b"Traceback", resp.content)


@override_settings(DEBUG=False, ROOT_URLCONF="core.error_handler_urls")
class Custom500Tests(TestCase):
    def test_500_custom_page_no_traceback(self):
        client = Client(raise_request_exception=False)
        resp = client.get("/boom/")
        self.assertEqual(resp.status_code, 500)
        self.assertTemplateUsed(resp, "errors/500.html")
        self.assertNotIn(b"Traceback", resp.content)
