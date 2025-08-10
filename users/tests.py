"""Tests for the users app."""

from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from io import BytesIO
import mongomock
from mongoengine import connect, disconnect
from PIL import Image
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import Review
from users.tasks import cleanup_expired_sessions, purge_inactive_users

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )  # nosec B106
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username="admin", password="adminpass"
        )  # nosec B106
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)


@override_settings(SECURE_SSL_REDIRECT=False)
class UserPauseReactivateTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )  # nosec B106
        self.user = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_pause_and_reactivate_user(self):
        pause_url = reverse(
            "pause-user", kwargs={"version": "v1", "user_id": self.user.id}
        )
        reactivate_url = reverse(
            "reactivate-user", kwargs={"version": "v1", "user_id": self.user.id}
        )

        response = self.client.post(pause_url)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_paused)

        response = self.client.post(reactivate_url)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_paused)


class RemoveExpiredTokensCommandTest(TestCase):
    def test_removes_only_expired_tokens(self):
        old_user = User.objects.create_user(
            username="old", email="old@example.com", password="pass"
        )  # nosec B106
        old_user.date_joined = timezone.now() - timedelta(days=2)
        old_user.save(update_fields=["date_joined"])

        recent_user = User.objects.create_user(
            username="new", email="new@example.com", password="pass"
        )  # nosec B106

        call_command("remove_expired_verification_tokens", days=1)

        old_user.refresh_from_db()
        recent_user.refresh_from_db()

        self.assertIsNone(old_user.verification_token)
        self.assertIsNotNone(recent_user.verification_token)


class CleanupExpiredSessionsTaskTest(TestCase):
    def test_deletes_only_expired_sessions(self):
        past = timezone.now() - timedelta(days=1)
        future = timezone.now() + timedelta(days=1)
        Session.objects.create(session_key="past", session_data="", expire_date=past)
        Session.objects.create(
            session_key="future", session_data="", expire_date=future
        )

        cleanup_expired_sessions.run()

        self.assertFalse(Session.objects.filter(session_key="past").exists())
        self.assertTrue(Session.objects.filter(session_key="future").exists())


class PurgeInactiveUsersTaskTest(TestCase):
    def test_deletes_only_inactive_users_past_retention(self):
        retention = getattr(settings, "PERSONAL_DATA_RETENTION_DAYS", 365)
        old_date = timezone.now() - timedelta(days=retention + 1)

        inactive_old = User.objects.create_user(
            username="oldinactive", password="pass", is_active=False
        )  # nosec B106
        inactive_old.last_login = old_date
        inactive_old.save(update_fields=["last_login"])

        inactive_recent = User.objects.create_user(
            username="recentinactive", password="pass", is_active=False
        )  # nosec B106
        inactive_recent.last_login = timezone.now()
        inactive_recent.save(update_fields=["last_login"])

        purge_inactive_users.run()

        self.assertFalse(User.objects.filter(id=inactive_old.id).exists())
        self.assertTrue(User.objects.filter(id=inactive_recent.id).exists())


class UserAvatarValidationTest(TestCase):
    def test_rejects_invalid_format(self):
        user = User.objects.create_user(username="a", password="pass")  # nosec B106
        gif_bytes = (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
            b"\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02L\x01\x00;"
        )
        user.avatar = SimpleUploadedFile(
            "avatar.gif", gif_bytes, content_type="image/gif"
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_rejects_large_file(self):
        user = User.objects.create_user(username="b", password="pass")  # nosec B106
        file_obj = BytesIO()
        Image.effect_noise((3000, 3000), 100).convert("RGB").save(
            file_obj, format="JPEG", quality=100
        )
        file_obj.seek(0)
        user.avatar = SimpleUploadedFile(
            "large.jpg", file_obj.read(), content_type="image/jpeg"
        )
        with self.assertRaises(ValidationError):
            user.full_clean()


@override_settings(SECURE_SSL_REDIRECT=False)
class UserDataExportViewTest(TestCase):
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
        Review.drop_collection()
        self.user = User.objects.create_user(
            username="export", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        order = Order.objects.create(user=self.user, total_price=20)
        OrderItem.objects.create(
            order=order, product_name="Item", quantity=1, unit_price=20
        )
        product = Product.objects.create(
            _id="507f1f77bcf86cd799439016",
            product_name="Prod",
            category="Test",
            description="Desc",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        Review.objects.create(
            user_id=self.user.pk,
            product=product,
            rating=5,
            comment="Great",
            status="approved",
            created_at=datetime.utcnow(),
        )

    def test_exports_user_data(self):
        url = reverse("user-data-export", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["username"], "export")
        self.assertEqual(len(data["orders"]), 1)
        self.assertEqual(len(data["reviews"]), 1)
        self.assertEqual(data["orders"][0]["items"][0]["product_name"], "Item")
