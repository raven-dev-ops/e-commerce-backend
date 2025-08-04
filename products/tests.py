# products/tests.py

from django.test import TestCase, override_settings
from mongoengine import connect, disconnect
import mongomock
from products.models import Product
from products.serializers import ProductSerializer
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from products.utils import send_low_stock_notification
from products.tasks import send_low_stock_email


class ProductModelSerializerTest(TestCase):
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
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439011",
            product_name="Test Soap",
            category="Bath",
            description="A soothing soap",
            price=9.99,
            ingredients=["Sodium hydroxide", "Water", "Fragrance"],
            images=["http://example.com/image1.jpg"],
            variations=[{"color": "blue"}, {"size": "small"}],
            weight=0.25,
            dimensions="3x3x1",
            benefits=["Moisturizing", "Gentle"],
            scent_profile="Lavender",
            variants=[{"type": "bar"}, {"type": "liquid"}],
            tags=["soap", "bath"],
            availability=True,
            inventory=100,
            reserved_inventory=5,
            average_rating=4.5,
            review_count=10,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Soap")

    def test_product_serializer(self):
        serializer = ProductSerializer(instance=self.product)
        data = serializer.data
        self.assertEqual(data["product_name"], "Test Soap")
        self.assertEqual(data["price"], "9.99")  # Decimal serialized as string
        self.assertIn("bath", [tag.lower() for tag in data["tags"]])
        self.assertEqual(data["average_rating"], 4.5)
        self.assertEqual(data["review_count"], 10)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ProductAPITestCase(TestCase):
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
        self.client = APIClient()
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439099",
            product_name="API Soap",
            category="Bath",
            description="A soap via API",
            price=5.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )

    def test_list_products_endpoint(self):
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_name"], "API Soap")

    def test_retrieve_product_endpoint(self):
        url = reverse("product-detail", args=[self.product._id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["_id"], self.product._id)
        self.assertEqual(response.data["product_name"], "API Soap")


class ProductTasksTestCase(TestCase):
    @override_settings(
        DEFAULT_FROM_EMAIL="from@example.com", ADMIN_EMAIL="admin@example.com"
    )
    @patch("products.tasks.send_mail")
    def test_send_low_stock_email_task(self, mock_send_mail):
        send_low_stock_email("Soap", "1", 2)
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[0]
        self.assertEqual(args[0], "Low Stock Alert: Soap")
        self.assertIn("Current Stock: 2", args[1])
        self.assertEqual(args[2], "from@example.com")
        self.assertEqual(args[3], ["admin@example.com"])

    @override_settings(ADMIN_EMAIL="admin@example.com")
    @patch("products.utils.send_low_stock_email.delay")
    def test_send_low_stock_notification_queues_task(self, mock_delay):
        send_low_stock_notification("Soap", "1", 3)
        mock_delay.assert_called_once_with("Soap", "1", 3)
