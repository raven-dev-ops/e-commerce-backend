from django.test import TestCase, override_settings
from django.core.cache import cache
from django.core.management import call_command
from unittest.mock import patch

from products.models import Product, Category
from products.utils import send_low_stock_notification
from products.tasks import send_low_stock_email, upload_product_image_to_s3
from backend.tests.utils import MongoTestCase


class ProductTasksTestCase(MongoTestCase):
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


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class PrewarmCachesCommandTest(MongoTestCase):
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


@override_settings(
    SECURE_SSL_REDIRECT=False,
    ERP_API_URL="https://erp.example.com",
    ERP_API_KEY="testkey",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ERPInventorySyncTest(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        self.product = Product.objects.create(
            _id="erp1",
            product_name="ERP Soap",
            category="Bath",
            description="desc",
            price=1.0,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=0,
            reserved_inventory=0,
        )

    @patch("erp.client.requests.get")
    def test_sync_inventory_command_updates_product(self, mock_get):
        mock_get.return_value.json.return_value = {"inventory": 25}
        mock_get.return_value.raise_for_status.return_value = None

        call_command("sync_inventory_from_erp")
        self.product.reload()
        self.assertEqual(self.product.inventory, 25)
        mock_get.assert_called_with(
            "https://erp.example.com/inventory/erp1",
            headers={"Authorization": "Bearer testkey"},
            timeout=5,
        )

