from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security-related HTTP headers."""

    def process_response(self, request, response):
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'",
        )
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload",
        )
        return response

