# products/tests.py

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from mongoengine import connect, disconnect
import mongomock
from products.models import Product, Category
from products.serializers import ProductSerializer
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from products.utils import send_low_stock_notification
from products.tasks import send_low_stock_email, upload_product_image_to_s3
from orders.models import Order, OrderItem
from products.services import get_recommended_products
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command


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
        self.assertEqual(data["slug"], "test-soap")
        self.assertEqual(data["price"], "9.99")  # Decimal serialized as string
        self.assertIn("bath", [tag.lower() for tag in data["tags"]])
        self.assertEqual(data["average_rating"], 4.5)
        self.assertEqual(data["review_count"], 10)

    def test_product_slug_unique(self):
        second = Product.objects.create(
            _id="507f1f77bcf86cd799439012",
            product_name="Test Soap",
            category="Bath",
            description="Another soap",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        self.assertNotEqual(self.product.slug, second.slug)

    def test_soft_delete_and_restore(self):
        product_id = self.product._id
        self.product.delete()
        self.assertIsNone(Product.objects(_id=product_id).first())
        deleted = Product.all_objects(_id=product_id).first()
        self.assertIsNotNone(deleted)
        self.assertTrue(deleted.is_deleted)
        deleted.restore()
        self.assertIsNotNone(Product.objects(_id=product_id).first())


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
        User = get_user_model()
        self.regular_user = User.objects.create_user(
            username="regular", password="pass"
        )  # nosec B106
        self.staff_user = User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )  # nosec B106

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
class ProductBulkAPITestCase(TestCase):
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
        User = get_user_model()
        self.staff_user = User.objects.create_user(
            username="staffbulk", password="pass", is_staff=True
        )  # nosec B106

    def test_bulk_import_creates_products(self):
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


class ProductTasksTestCase(TestCase):
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

    @override_settings(AWS_S3_BUCKET="test-bucket")
    @patch("products.tasks.boto3.client")
    def test_upload_product_image_to_s3_task(self, mock_client):
        product = Product.objects.create(
            _id="img1",
            product_name="Img Soap",
            category="Bath",
            description="desc",
            price=5.0,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=1,
            reserved_inventory=0,
        )
        mock_s3 = mock_client.return_value
        mock_s3.upload_fileobj.return_value = None
        upload_product_image_to_s3(str(product._id), "test.jpg", b"data")
        mock_s3.upload_fileobj.assert_called_once()
        updated = Product.objects.get(_id="img1")
        self.assertEqual(len(updated.images), 1)
        self.assertTrue(updated.images[0].endswith("test.jpg"))


class ProductRecommendationServiceTestCase(TestCase):
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
        User = get_user_model()
        self.user = User.objects.create_user(
            username="recuser", password="pass"
        )  # nosec B106
        Product.objects.create(
            _id="p1",
            product_name="Soap A",
            category="Bath",
            description="desc",
            price=1.0,
            average_rating=4.0,
        )
        Product.objects.create(
            _id="p2",
            product_name="Soap B",
            category="Bath",
            description="desc",
            price=1.0,
            average_rating=5.0,
        )
        Product.objects.create(
            _id="p3",
            product_name="Lotion C",
            category="Beauty",
            description="desc",
            price=1.0,
        )
        order = Order.objects.create(
            user=self.user,
            total_price=1.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order, product_name="Soap A", quantity=1, unit_price=1.0
        )

    def test_recommend_products_from_purchase_history(self):
        recommendations = get_recommended_products(self.user)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].product_name, "Soap B")

    def test_returns_empty_list_for_new_user(self):
        User = get_user_model()
        new_user = User.objects.create_user(
            username="newuser", password="pass"
        )  # nosec B106
        self.assertEqual(get_recommended_products(new_user), [])


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class PrewarmCachesCommandTest(TestCase):
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
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439099",
            product_name="Cache Soap",
            category="Bath",
            description="desc",
            price=1.0,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        Category.objects.create(
            _id="507f1f77bcf86cd799439098", name="Bath", description=""
        )
        cache.clear()

    def test_command_warms_expected_caches(self):
        call_command("prewarm_caches")
        self.assertIsNotNone(cache.get("product_list"))
        self.assertIsNotNone(cache.get(f"product:{self.product.slug}"))
        self.assertIsNotNone(cache.get("category_list"))
