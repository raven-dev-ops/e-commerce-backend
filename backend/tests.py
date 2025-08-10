from django.test import SimpleTestCase, TestCase
from django.urls import reverse, resolve
from unittest.mock import patch
from mongoengine import connect, disconnect
import mongomock
from products.models import Product
from celery import shared_task
from backend.celery_monitoring import (
    TASK_FAILURES,
    TASK_SUCCESSES,
)


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
        query = "{ products { productName category } }"
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
