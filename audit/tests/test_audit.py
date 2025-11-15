from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Product
from audit.models import AuditLog
from backend.tests.utils import MongoTestCase


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class AuditLogMiddlewareTest(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        self.client = APIClient()
        User = get_user_model()
        self.staff_user = User.objects.create_user(username="staff", is_staff=True)
        self.client.force_authenticate(self.staff_user)

    def test_audit_log_created_for_staff_modification(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        payload = {
            "product_name": "Audit Soap",
            "category": "Bath",
            "description": "desc",
            "price": "1.00",
            "ingredients": [],
            "benefits": [],
            "inventory": 5,
            "reserved_inventory": 0,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.user, self.staff_user)
        self.assertEqual(log.method, "POST")
        self.assertEqual(log.path, url)
