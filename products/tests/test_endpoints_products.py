from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from products.models import Product
from backend.tests.utils import MongoTestCase
from django.core.cache import cache


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ProductAPITestCase(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        cache.clear()
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
        user_model = get_user_model()
        self.regular_user = user_model.objects.create_user(
            username="regular", password="pass"  # nosec B106
        )
        self.staff_user = user_model.objects.create_user(
            username="staff", password="pass", is_staff=True  # nosec B106
        )

    def test_list_products_endpoint(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_name"], "API Soap")
        self.assertEqual(response.data["results"][0]["slug"], self.product.slug)

    def test_client_defined_page_size(self):
        for i in range(15):
            Product.objects.create(
                _id=f"507f1f77bcf86cd7994391{i:02}",
                product_name=f"API Soap {i}",
                category="Bath",
                description="A soap via API",
                price=5.00,
                ingredients=[],
                benefits=[],
                tags=[],
                inventory=10,
                reserved_inventory=0,
            )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"page_size": 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)

    def test_page_size_has_upper_bound(self):
        for i in range(110):
            Product.objects.create(
                _id=f"bulk{i}",
                product_name=f"Bulk {i}",
                category="Bath",
                description="desc",
                price=1.00,
                ingredients=[],
                benefits=[],
                tags=[],
                inventory=1,
                reserved_inventory=0,
            )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"page_size": 200})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 111)
        self.assertEqual(len(response.data["results"]), 100)

    def test_retrieve_product_endpoint(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["_id"], self.product._id)
        self.assertEqual(response.data["product_name"], "API Soap")
        self.assertEqual(response.data["slug"], self.product.slug)

    def test_product_detail_is_cached(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        cache_key = f"product:{self.product.slug}"
        self.assertIsNone(cache.get(cache_key))
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertIsNotNone(cache.get(cache_key))
        Product.drop_collection()
        second = self.client.get(url)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["_id"], self.product._id)

    def test_product_list_is_cached(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        cache_key = "product_list"
        self.assertIsNone(cache.get(cache_key))
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["count"], 1)
        self.assertIsNotNone(cache.get(cache_key))
        Product.drop_collection()
        second = self.client.get(url)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["count"], 1)

    def test_filter_products_by_category(self):
        Product.objects.create(
            _id="507f1f77bcf86cd799439200",
            product_name="Kitchen Soap",
            category="Kitchen",
            description="Degreaser",
            price=12.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=5,
            reserved_inventory=0,
        )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"category": "Kitchen"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["category"], "Kitchen")

    def test_filter_products_by_price_range(self):
        Product.objects.create(
            _id="507f1f77bcf86cd799439201",
            product_name="Premium Soap",
            category="Bath",
            description="Luxurious",
            price=15.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=5,
            reserved_inventory=0,
        )
        Product.objects.create(
            _id="507f1f77bcf86cd799439202",
            product_name="Cheap Soap",
            category="Bath",
            description="Budget",
            price=1.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=5,
            reserved_inventory=0,
        )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"price__gte": 5, "price__lte": 15})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        prices = sorted(float(p["price"]) for p in response.data["results"])
        self.assertEqual(prices, [5.0, 15.0])

    def test_scheduled_publish_and_unpublish(self):
        from django.utils import timezone
        from datetime import timedelta

        future = timezone.now() + timedelta(days=1)
        past = timezone.now() - timedelta(days=1)
        Product.objects.create(
            _id="507f1f77bcf86cd799439203",
            product_name="Future Soap",
            category="Bath",
            description="Not yet",
            price=2.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=1,
            reserved_inventory=0,
            publish_at=future,
        )
        Product.objects.create(
            _id="507f1f77bcf86cd799439204",
            product_name="Old Soap",
            category="Bath",
            description="Expired",
            price=2.00,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=1,
            reserved_inventory=0,
            unpublish_at=past,
        )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_name"], "API Soap")

    def test_non_staff_cannot_create_product(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        payload = {
            "product_name": "New Soap",
            "category": "Bath",
            "description": "Nice",
            "price": "3.00",
            "ingredients": ["Water"],
            "benefits": ["Clean"],
            "inventory": 5,
            "reserved_inventory": 0,
        }
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_product(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        payload = {
            "product_name": "Staff Soap",
            "category": "Bath",
            "description": "Nice",
            "price": "3.00",
            "ingredients": ["Water"],
            "benefits": ["Clean"],
            "inventory": 5,
            "reserved_inventory": 0,
        }
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("slug", response.data)

    def test_non_staff_cannot_update_product(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(url, {"product_name": "Nope"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_staff_can_update_product(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(url, {"product_name": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_delete_product(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_delete_product(self):
        url = reverse(
            "product-detail",
            kwargs={"slug": self.product.slug, "version": "v1"},
        )
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    @patch("products.search._es_client.search")
    def test_search_products_endpoint(self, mock_search):
        mock_search.return_value = {
            "hits": {"hits": [{"_source": {"product_name": "API Soap"}}]}
        }
        url = reverse("product-search", kwargs={"version": "v1"})
        response = self.client.get(url, {"q": "soap"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["product_name"], "API Soap")
        mock_search.assert_called_once()


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ProductBulkAPITestCase(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        self.client = APIClient()
        user_model = get_user_model()
        self.staff_user = user_model.objects.create_user(
            username="staffbulk", password="pass", is_staff=True  # nosec B106
        )

    def test_bulk_import_creates_products(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_data = (
            "product_name,category,description,price,inventory,ingredients,benefits,tags\n"
            "Bulk Soap,Bath,Desc,3.00,5,Water|Lye,Clean,Bath\n"
            "Bulk Lotion,Bath,Moisturizer,5.50,10,Water,Moisturize,Skincare\n"
        )
        file = SimpleUploadedFile(
            "products.csv", csv_data.encode("utf-8"), content_type="text/csv"
        )
        url = reverse("product-bulk-import", kwargs={"version": "v1"})
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["imported"], 2)
        self.assertEqual(Product.objects.count(), 2)

    def test_bulk_export_returns_csv(self):
        Product.objects.create(
            _id="prodexp1",
            product_name="Export Soap",
            category="Bath",
            description="desc",
            price=5.0,
            ingredients=["Water"],
            benefits=["Clean"],
            tags=["Bath"],
            inventory=10,
            reserved_inventory=0,
        )
        url = reverse("product-bulk-export", kwargs={"version": "v1"})
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        lines = response.content.decode("utf-8").splitlines()
        self.assertEqual(
            lines[0],
            "product_name,category,description,price,inventory,ingredients,benefits,tags",
        )
        self.assertIn("Export Soap", lines[1])


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ValidationErrorFormatTestCase(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin", password="pass", is_staff=True  # nosec B106
        )

    def test_structured_validation_errors(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/products/",
            data={},
            format="json",
            secure=True,
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("errors", data)
        self.assertIsInstance(data["errors"], list)
        fields = {err.get("field") for err in data["errors"]}  # type: ignore[union-attr]
        self.assertIn("product_name", fields)

