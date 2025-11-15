from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from giftcards.models import GiftCard


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class GiftCardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="giftuser", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.list_url = reverse("giftcard-list", kwargs={"version": "v1"})
        self.redeem_url = reverse("giftcard-redeem", kwargs={"version": "v1"})

    def test_purchase_creates_giftcard(self):
        response = self.client.post(self.list_url, {"amount": "25.00"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(GiftCard.objects.filter(id=response.data["id"]).exists())

    def test_redeem_giftcard(self):
        card = GiftCard.objects.create(amount=10, balance=10)
        response = self.client.post(self.redeem_url, {"code": card.code}, format="json")
        self.assertEqual(response.status_code, 200)
        card.refresh_from_db()
        self.assertFalse(card.is_active)
        self.assertEqual(card.balance, 0)
        self.assertEqual(card.redeemed_by, self.user)
