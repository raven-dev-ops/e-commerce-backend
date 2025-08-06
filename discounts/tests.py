"""Tests for the discounts app."""

from django.test import TestCase, override_settings
from django.urls import reverse
from mongoengine import connect, disconnect
import mongomock
from rest_framework.test import APIClient
from django.core.cache import cache
from django.contrib.auth import get_user_model
from mongoengine.errors import NotUniqueError

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

    def test_code_is_normalized_to_uppercase(self):
        discount = Discount.objects.create(
            code="testcode", discount_type="fixed", value=5
        )
        self.assertEqual(discount.code, "TESTCODE")

    def test_code_is_case_insensitive_unique(self):
        Discount.objects.create(code="SAVE10", discount_type="fixed", value=5)
        with self.assertRaises(NotUniqueError):
            Discount.objects.create(code="save10", discount_type="percentage", value=10)


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
        cache.clear()
        self.client = APIClient()
        self.category = Category.objects.create(
            _id="507f1f77bcf86cd799439014", name="Bath", description="Bath"
        )
        User = get_user_model()
        self.user = User.objects.create_user("tester", "test@example.com", "pass1234")

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

    def test_category_list_is_cached(self):
        url = reverse("category-list-create")
        cache_key = "category_list"
        self.assertIsNone(cache.get(cache_key))
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertIsNotNone(cache.get(cache_key))
        Category.drop_collection()
        second = self.client.get(url)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.data), 1)

    def test_category_cache_invalidated_on_update(self):
        list_url = reverse("category-list-create")
        cache_key = "category_list"
        self.client.get(list_url)
        self.assertIsNotNone(cache.get(cache_key))
        detail_url = reverse("category-detail", args=[self.category.id])
        self.client.force_authenticate(user=self.user)
        update_response = self.client.patch(
            detail_url, {"name": "Updated"}, format="json"
        )
        self.client.force_authenticate(user=None)
        self.assertEqual(update_response.status_code, 200)
        self.assertIsNone(cache.get(cache_key))
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data[0]["name"], "Updated")
