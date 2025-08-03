from django.test import TestCase


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
        self.assertEqual(response.json().get("status"), "ok")
