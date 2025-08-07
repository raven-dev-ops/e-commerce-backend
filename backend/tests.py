from django.test import SimpleTestCase, TestCase
from django.urls import reverse, resolve
from unittest.mock import patch


class SecurityHeadersMiddlewareTest(TestCase):
    def test_security_headers_are_present(self):
        response = self.client.get("/", secure=True, HTTP_HOST="localhost")
        self.assertEqual(
            response.headers.get("Permissions-Policy"), "geolocation=(), microphone=()"
        )
        self.assertEqual(
            response.headers.get("Content-Security-Policy"), "default-src 'self'"
        )
        self.assertEqual(
            response.headers.get("Strict-Transport-Security"),
            "max-age=63072000; includeSubDomains; preload",
        )


class HealthEndpointTest(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health/", secure=True, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("database"), "ok")

    @patch("backend.urls.connection.ensure_connection", side_effect=Exception)
    def test_health_reports_database_unavailable(self, mocked_ensure):
        response = self.client.get("/health/", secure=True, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("database"), "unavailable")


class APIDocumentationTest(SimpleTestCase):
    def test_schema_urls_are_configured(self):
        self.assertEqual(reverse("schema-json"), "/api/schema/")
        self.assertEqual(reverse("schema-swagger-ui"), "/api/docs/")
        resolver = resolve("/api/docs/")
        self.assertEqual(resolver.url_name, "schema-swagger-ui")


class RobotsTxtTest(SimpleTestCase):
    def test_robots_txt_served(self):
        response = self.client.get("/robots.txt", secure=True, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn("User-agent: *", response.content.decode())


class APIVersioningTest(TestCase):
    def test_supported_version_resolves(self):
        response = self.client.get(
            "/api/v1/users/profile/", secure=True, HTTP_HOST="localhost"
        )
        self.assertNotEqual(response.status_code, 404)

    def test_unsupported_version_returns_404(self):
        response = self.client.get(
            "/api/v2/users/profile/", secure=True, HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 404)
