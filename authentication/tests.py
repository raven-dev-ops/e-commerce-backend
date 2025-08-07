from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

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
        import json

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
