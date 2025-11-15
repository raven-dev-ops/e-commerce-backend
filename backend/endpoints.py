import os

# backend/endpoints.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from backend.schema import schema
from backend.graphql import CachedGraphQLView
from backend.views import PurgeCacheView, RateLimitStatusView


def home(request):
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "unavailable"

    raw_status = os.getenv("CI_LAST_TEST_STATUS", "unknown")
    status_lower = raw_status.lower()
    tests_passed = status_lower in {"passed", "success", "green"}

    tests_info = {
        "passed": tests_passed,
        "status": raw_status,
        "last_run": os.getenv("CI_LAST_TEST_RUN", "unknown"),
        "branch": os.getenv("CI_LAST_TEST_BRANCH", "unknown"),
        "commit": os.getenv(
            "CI_LAST_TEST_COMMIT", os.getenv("GIT_COMMIT_SHA", "unknown")
        ),
        "url": os.getenv("CI_LAST_TEST_URL", None),
    }

    logging_info = {
        "level": settings.LOGGING.get("root", {}).get("level", "INFO"),
        "dd_trace_enabled": os.getenv("DD_TRACE_ENABLED", "false"),
        "otel_trace_enabled": os.getenv("OTEL_TRACE_ENABLED", "false"),
    }

    return JsonResponse(
        {
            "message": "Welcome to the e-commerce backend API!",
            "status": {
                "liveness": "ok",
                "database": db_status,
            },
            "tests": tests_info,
            "logging": logging_info,
            "version": {
                "release": os.getenv("HEROKU_RELEASE_VERSION", "unknown"),
                "commit": os.getenv("GIT_COMMIT_SHA", "unknown"),
            },
        }
    )


def custom_404(request, exception=None):
    return JsonResponse({"error": "Endpoint not found"}, status=404)


def readiness(request):
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    status_code = 200 if db_status == "ok" else 503
    return JsonResponse({"status": "ok", "database": db_status}, status=status_code)


def liveness(request):
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    content = "User-agent: *\nDisallow: /admin/\n"
    return HttpResponse(content, content_type="text/plain")


def security_txt(request):
    content = "Contact: mailto:security@example.com\n"
    return HttpResponse(content, content_type="text/plain")


schema_view = get_schema_view(
    openapi.Info(
        title="E-Commerce API",
        default_version="v1",
        description="API documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

api_urlpatterns = [
    path("users/", include("users.endpoints")),
    path("products/", include("products.endpoints")),
    path("orders/", include("orders.endpoints")),
    path("cart/", include("cart.endpoints")),
    path("payments/", include("payments.endpoints")),
    path("discounts/", include("discounts.endpoints")),
    path("reviews/", include("reviews.endpoints")),
    path("giftcards/", include("giftcards.endpoints")),
    path("referrals/", include("referrals.endpoints")),
    path("notifications/", include("notifications.endpoints")),
    path("authentication/", include("authentication.endpoints")),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/social/", include("allauth.socialaccount.urls")),
    path(
        "graphql/", csrf_exempt(CachedGraphQLView.as_view(schema=schema, graphiql=True))
    ),
    path("cache/purge/", PurgeCacheView.as_view(), name="purge-cache"),
    path("rate-limit/", RateLimitStatusView.as_view(), name="rate-limit"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home),
    path("health/live/", liveness),
    path("health/ready/", readiness),
    path("health/", readiness),
    path(".well-known/security.txt", security_txt),
    path("robots.txt", robots_txt),
    path("api/<str:version>/", include(api_urlpatterns)),
    path("api/schema/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

handler404 = "backend.endpoints.custom_404"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
