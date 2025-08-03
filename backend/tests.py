from django.test import TestCase


class SecurityHeadersMiddlewareTest(TestCase):
    def test_security_headers_are_present(self):
        response = self.client.get('/', secure=True, HTTP_HOST='localhost')
        self.assertEqual(
            response.headers.get('Permissions-Policy'),
            'geolocation=(), microphone=()'
        )
        self.assertEqual(
            response.headers.get('Content-Security-Policy'),
            "default-src 'self'"
        )
        self.assertEqual(
            response.headers.get('Strict-Transport-Security'),
            'max-age=63072000; includeSubDomains; preload'
        )
