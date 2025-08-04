"""Tests for the discounts app."""

from django.test import TestCase, override_settings
from django.urls import reverse
from mongoengine import connect, disconnect
import mongomock
from rest_framework.test import APIClient

from discounts.models import Discount
from products.models import Product, Category


class DiscountModelTest(TestCase):
    """Tests for the Discount model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure we use an in-memory MongoDB for tests
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
        Discount.drop_collection()
        Product.drop_collection()
        Category.drop_collection()
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439012",
            product_name="Test Product",
            category="Bath",
            description="A test product",
            price=10.0,
            ingredients=[],
            images=[],
            variations=[],
            benefits=[],
            tags=[],
        )
        self.category = Category.objects.create(
            _id="507f1f77bcf86cd799439013", name="Soaps", description="Soap cat"
        )

    def test_discount_str_and_defaults(self):
        discount = Discount.objects.create(
            code="TEST10",
            discount_type="percentage",
            value=10,
            target_products=[self.product],
            target_categories=[self.category],
        )

        self.assertEqual(str(discount), "TEST10 (percentage)")
        self.assertTrue(discount.is_active)
        self.assertEqual(discount.times_used, 0)
        self.assertFalse(discount.is_automatic)
        self.assertFalse(discount.is_free_shipping)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class DiscountAPITestCase(TestCase):
    """API tests for Discount endpoints."""

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
        Discount.drop_collection()
        self.client = APIClient()
        self.discount = Discount.objects.create(
            code="API10", discount_type="fixed", value=5.0
        )

    def test_list_discounts_endpoint(self):
        url = reverse("discount-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "API10")

    def test_retrieve_discount_endpoint(self):
        url = reverse("discount-detail", args=[self.discount.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["code"], "API10")


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class CategoryAPITestCase(TestCase):
    """API tests for Category endpoints within the discounts app."""

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
        Category.drop_collection()
        self.client = APIClient()
        self.category = Category.objects.create(
            _id="507f1f77bcf86cd799439014", name="Bath", description="Bath"
        )

    def test_list_categories_endpoint(self):
        url = reverse("category-list-create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Bath")

    def test_retrieve_category_endpoint(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Bath")
