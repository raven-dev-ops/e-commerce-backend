from django.utils.deprecation import MiddlewareMixin
import uuid
import contextvars
import logging


correlation_id_ctx = contextvars.ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """Inject correlation ID into log records."""

    def filter(self, record):  # type: ignore[override]
        record.correlation_id = correlation_id_ctx.get()
        return True


class CorrelationIdMiddleware(MiddlewareMixin):
    """Assign a correlation ID to each request and response."""

    header = "X-Correlation-ID"

    def process_request(self, request):
        correlation_id = request.headers.get(self.header, str(uuid.uuid4()))
        correlation_id_ctx.set(correlation_id)
        request.correlation_id = correlation_id

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", correlation_id_ctx.get())
        if correlation_id:
            response[self.header] = correlation_id
        correlation_id_ctx.set(None)
        return response


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
