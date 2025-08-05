from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from decimal import Decimal

from orders.models import Order, OrderItem
from .models import Payment, Transaction
from products.models import Product
from mongoengine import connect, disconnect
import mongomock


class PaymentsModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="john", password="pass")

        self.payment = Payment.objects.create(
            user=self.user,
            invoice="INV1001",
            amount=Decimal("150.00"),
            method="CC",
        )

        self.transaction = Transaction.objects.create(
            payment=self.payment,
            status="Completed",
        )

    def test_payment_str(self):
        self.assertEqual(
            str(self.payment), f"Payment {self.payment.id} - john - 150.00"
        )

    def test_transaction_str(self):
        self.assertIn("Transaction", str(self.transaction))
        self.assertIn("Completed", str(self.transaction))


@override_settings(SECURE_SSL_REDIRECT=False)
class StripeWebhookViewTests(TestCase):
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
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pass")
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439500",
            product_name="Widget",
            category="Test",
            price=10.0,
            inventory=5,
            reserved_inventory=1,
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=10.0,
            shipping_cost=0,
            tax_amount=0,
            payment_intent_id="pi_test",
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=self.order,
            product_name=self.product.product_name,
            quantity=1,
            unit_price=10.0,
        )

    @patch("stripe.Webhook.construct_event")
    def test_payment_intent_succeeded_sets_processing(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}},
        }

        response = self.client.post(
            reverse("stripe-webhook"), data={}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PROCESSING)
        self.product.reload()
        self.assertEqual(self.product.reserved_inventory, 1)

    @patch("stripe.Webhook.construct_event")
    def test_payment_intent_failed_sets_failed(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_test"}},
        }

        response = self.client.post(
            reverse("stripe-webhook"), data={}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.FAILED)
        self.product.reload()
        self.assertEqual(self.product.reserved_inventory, 0)
