# users/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
