from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from referrals.models import ReferralCode


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class ReferralCodeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="refuser")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.list_url = reverse("referralcode-list", kwargs={"version": "v1"})
        self.track_url = reverse("referralcode-track", kwargs={"version": "v1"})

    def test_create_referral_code(self):
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ReferralCode.objects.filter(id=response.data["id"]).exists())

    def test_track_referral_code(self):
        code = ReferralCode.objects.create(created_by=self.user)
        response = self.client.post(self.track_url, {"code": code.code}, format="json")
        self.assertEqual(response.status_code, 200)
        code.refresh_from_db()
        self.assertEqual(code.usage_count, 1)
