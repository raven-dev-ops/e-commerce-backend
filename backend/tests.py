from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse, resolve, path
from django.core.cache import cache
from unittest.mock import patch
from mongoengine import connect, disconnect
import mongomock
from products.models import Product, Category
from celery import shared_task
from backend.celery_monitoring import (
    TASK_FAILURES,
    TASK_SUCCESSES,
)
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.http import HttpResponse
import gzip


def big_view(request):
    return HttpResponse("x" * 1000)


urlpatterns = [path("big/", big_view)]


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


class CorsPreflightCacheTest(TestCase):
    def test_preflight_response_is_cached(self):
        response = self.client.options(
            "/health/",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ORIGIN="https://twiinz-beard-frontend.netlify.app",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Max-Age"), "86400")


@override_settings(ROOT_URLCONF=__name__)
class GZipMiddlewareTest(SimpleTestCase):
    def test_response_is_gzipped(self):
        response = self.client.get(
            "/big/",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_ACCEPT_ENCODING="gzip",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Encoding"], "gzip")
        self.assertEqual(gzip.decompress(response.content), b"x" * 1000)


class CorrelationIdMiddlewareTest(TestCase):
    def test_correlation_id_added(self):
        response = self.client.get("/health/", secure=True, HTTP_HOST="localhost")
        self.assertIn("X-Correlation-ID", response.headers)
        self.assertTrue(response.headers["X-Correlation-ID"])

    def test_existing_correlation_id_used(self):
        response = self.client.get(
            "/health/",
            secure=True,
            HTTP_HOST="localhost",
            HTTP_X_CORRELATION_ID="test-id",
        )
        self.assertEqual(response.headers["X-Correlation-ID"], "test-id")


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
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("database"), "unavailable")


class LivenessEndpointTest(TestCase):
    def test_liveness_returns_ok(self):
        response = self.client.get("/health/live/", secure=True, HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")


class RateLimitStatusViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ratelimit", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse("rate-limit", kwargs={"version": "v1"})

    def test_rate_limit_usage_reported(self):
        first = self.client.get(self.url, secure=True, HTTP_HOST="localhost")
        self.assertEqual(first.status_code, 200)
        data1 = first.json()["user"]
        self.assertEqual(data1["remaining"], data1["limit"] - 1)

        second = self.client.get(self.url, secure=True, HTTP_HOST="localhost")
        data2 = second.json()["user"]
        self.assertEqual(data2["remaining"], data1["remaining"] - 1)


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


class SecurityTxtTest(SimpleTestCase):
    def test_security_txt_served(self):
        response = self.client.get(
            "/.well-known/security.txt", secure=True, HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn("Contact: mailto:security@example.com", response.content.decode())


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


class GraphQLProductQueryTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disconnect()
        connect(
            "mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
        )

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        Product.drop_collection()
        Category.drop_collection()
        Category.objects.create(
            _id="bath",
            name="Bath",
            description="Bath items",
        )
        Product.objects.create(
            _id="507f1f77bcf86cd799439033",
            product_name="GraphQL Soap",
            category="Bath",
            description="Test product",
            price=2.0,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=5,
            reserved_inventory=0,
        )

    def test_products_query_returns_data(self):
        query = "{ products { productName category { name } } }"
        response = self.client.post(
            "/api/v1/graphql/",
            data={"query": query},
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["products"][0]["productName"], "GraphQL Soap")
        self.assertEqual(
            data["data"]["products"][0]["category"]["name"],
            "Bath",
        )


class GraphQLIntrospectionCacheTest(TestCase):
    def test_introspection_query_is_cached(self):
        cache.clear()
        introspection_query = (
            "query IntrospectionQuery { __schema { queryType { name } } }"
        )
        url = "/api/v1/graphql/"
        response = self.client.post(
            url,
            data={"query": introspection_query},
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 200)

        with patch(
            "graphene_django.views.GraphQLView.dispatch",
            side_effect=Exception("cache miss"),
        ):
            cached_response = self.client.post(
                url,
                data={"query": introspection_query},
                content_type="application/json",
                secure=True,
                HTTP_HOST="localhost",
            )

        self.assertEqual(cached_response.status_code, 200)


class GraphQLComplexityLimitTest(TestCase):
    @override_settings(GRAPHQL_MAX_COMPLEXITY=2)
    def test_complex_query_rejected(self):
        query = "{ products { productName category { name } } }"
        response = self.client.post(
            "/api/v1/graphql/",
            data={"query": query},
            content_type="application/json",
            secure=True,
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("errors", data)
        self.assertIn("too complex", data["errors"][0]["message"])


@override_settings(SECURE_SSL_REDIRECT=False)
class CachePurgeEndpointTest(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin", password="adminpass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_purge_clears_cache(self):
        cache.set("foo", "bar")
        url = reverse("purge-cache", kwargs={"version": "v1"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(cache.get("foo"))

    def test_non_admin_forbidden(self):
        user = get_user_model().objects.create_user(
            username="user", password="pass"
        )  # nosec B106
        client = APIClient()
        client.force_authenticate(user=user)
        url = reverse("purge-cache", kwargs={"version": "v1"})
        response = client.post(url)
        self.assertEqual(response.status_code, 403)


class CeleryMonitoringTest(TestCase):
    def test_task_metrics_recorded(self):
        """Ensure success and failure metrics are captured for tasks."""
        TASK_SUCCESSES._metrics.clear()
        TASK_FAILURES._metrics.clear()

        @shared_task(name="tests.success_task")
        def success_task():
            return "ok"

        @shared_task(name="tests.fail_task")
        def fail_task():
            raise Exception("boom")

        success_task.apply()
        with patch("backend.celery_monitoring.capture_exception") as mock_capture:
            fail_task.apply(throw=False)
            mock_capture.assert_called_once()

        success_value = TASK_SUCCESSES.labels(
            task_name="tests.success_task"
        )._value.get()
        failure_value = TASK_FAILURES.labels(task_name="tests.fail_task")._value.get()
        self.assertEqual(success_value, 1)
        self.assertEqual(failure_value, 1)
