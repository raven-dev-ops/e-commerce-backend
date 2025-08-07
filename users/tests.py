# users/tests.py

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from users.tasks import cleanup_expired_sessions

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
