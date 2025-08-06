# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.db import connection
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def home(request):
    return HttpResponse("Welcome to the e-commerce backend API!")


def custom_404(request, exception=None):
    return JsonResponse({"error": "Endpoint not found"}, status=404)


def health(request):
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return JsonResponse({"status": "ok", "database": db_status})


def robots_txt(request):
    content = "User-agent: *\nDisallow: /admin/\n"
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
    path("users/", include("users.urls")),
    path("products/", include("products.urls")),
    path("orders/", include("orders.urls")),
    path("cart/", include("cart.urls")),
    path("payments/", include("payments.urls")),
    path("discounts/", include("discounts.urls")),
    path("reviews/", include("reviews.urls")),
    path("authentication/", include("authentication.urls")),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/social/", include("allauth.socialaccount.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home),
    path("health/", health),
    path("robots.txt", robots_txt),
    path("api/v1/", include(api_urlpatterns)),
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

handler404 = "backend.urls.custom_404"
