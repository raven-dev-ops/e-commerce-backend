from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
import json
import pyotp

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )  # nosec B106
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))


@override_settings(SECURE_SSL_REDIRECT=False)
class EmailVerificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123",  # nosec B106
        )

    def test_login_blocked_until_verified(self):
        response = self.client.post(
            reverse("login", kwargs={"version": "v1"}),
            data=json.dumps({"email": "test@example.com", "password": "testpass123"}),
            content_type="application/json",
        )
        # Unverified users should not be able to log in
        self.assertEqual(response.status_code, 401)

    def test_verify_email_endpoint(self):
        token = self.user.verification_token
        url = reverse("verify-email", kwargs={"token": token, "version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminMFATest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="adminpass123",  # nosec B106
            is_staff=True,
        )
        self.user.email_verified = True
        self.user.mfa_secret = pyotp.random_base32()
        self.user.save()

    def test_admin_login_requires_otp(self):
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.check_password("adminpass123"))
        response = self.client.post(
            reverse("login", kwargs={"version": "v1"}),
            data=json.dumps({"email": "admin@example.com", "password": "adminpass123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_login_with_valid_otp(self):
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.check_password("adminpass123"))
        totp = pyotp.TOTP(self.user.mfa_secret)
        otp = totp.now()
        response = self.client.post(
            reverse("login", kwargs={"version": "v1"}),
            data=json.dumps(
                {
                    "email": "admin@example.com",
                    "password": "adminpass123",
                    "otp": otp,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tokens", response.json())


@override_settings(SECURE_SSL_REDIRECT=False)
class PausedUserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pause@example.com",
            email="pause@example.com",
            password="testpass123",  # nosec B106
        )
        self.user.email_verified = True
        self.user.is_paused = True
        self.user.save()

    def test_login_blocked_when_paused(self):
        response = self.client.post(
            reverse("login", kwargs={"version": "v1"}),
            data=json.dumps({"email": "pause@example.com", "password": "testpass123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Account is paused.")
