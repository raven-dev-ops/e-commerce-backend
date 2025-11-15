from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order
from backend.tests.utils import MongoTestCase


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderEndpointsTestCase(MongoTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="orderowner", password="pass"  # nosec B106
        )
        self.other_user = user_model.objects.create_user(
            username="otheruser", password="pass"  # nosec B106
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.order = Order.objects.create(
            user=self.user,
            total_price=20,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PROCESSING,
        )

    def test_list_orders_returns_only_user_orders(self):
        Order.objects.create(
            user=self.other_user,
            total_price=30,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

        url = reverse("order-list", kwargs={"version": "v1"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.order.id)

    def test_retrieve_order_must_belong_to_user(self):
        url = reverse(
            "order-detail",
            kwargs={"pk": self.order.id, "version": "v1"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Switch to other user and ensure 404
        self.client.force_authenticate(self.other_user)
        response_other = self.client.get(url)
        self.assertEqual(response_other.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_order_changes_status(self):
        url = reverse(
            "order-cancel",
            kwargs={"pk": self.order.id, "version": "v1"},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELED)

    def test_other_user_cannot_cancel_order(self):
        url = reverse(
            "order-cancel",
            kwargs={"pk": self.order.id, "version": "v1"},
        )
        self.client.force_authenticate(self.other_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_cancel_completed_order(self):
        self.order.status = Order.Status.DELIVERED
        self.order.save()

        url = reverse(
            "order-cancel",
            kwargs={"pk": self.order.id, "version": "v1"},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(SECURE_SSL_REDIRECT=False, SHIPMENT_WEBHOOK_SECRET="secret123")
class ShipmentWebhookTestCase(MongoTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="shipuser", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=10,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        self.client = APIClient()

    def _url(self):
        return reverse("shipment-webhook", kwargs={"version": "v1"})

    def test_missing_order_id_or_status_returns_400(self):
        response = self.client.post(
            self._url(),
            data={"order_id": self.order.id},
            format="json",
            HTTP_X_WEBHOOK_TOKEN="secret123",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_status_returns_400(self):
        response = self.client.post(
            self._url(),
            data={"order_id": self.order.id, "status": "invalid"},
            format="json",
            HTTP_X_WEBHOOK_TOKEN="secret123",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_not_found_returns_404(self):
        response = self.client.post(
            self._url(),
            data={"order_id": 9999, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN="secret123",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valid_update_changes_status(self):
        response = self.client.post(
            self._url(),
            data={"order_id": self.order.id, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN="secret123",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)

    @override_settings(SHIPMENT_WEBHOOK_SECRET="secret123")
    def test_invalid_token_returns_401(self):
        response = self.client.post(
            self._url(),
            data={"order_id": self.order.id, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN="wrong",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

