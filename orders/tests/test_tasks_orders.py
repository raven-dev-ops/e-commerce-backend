from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch

from orders.models import Order, OrderItem
from orders.tasks import (
    auto_cancel_stale_pending_orders,
    send_order_confirmation_email,
    send_order_status_sms,
)
from products.models import Category, Product


class OrderTasksTestCase(TestCase):
    @override_settings(DEFAULT_FROM_EMAIL="from@example.com")
    @patch("orders.tasks.send_mail")
    def test_send_order_confirmation_email_uses_send_mail(self, mock_send_mail):
        send_order_confirmation_email(123, "user@example.com")

        mock_send_mail.assert_called_once()
        subject, message, from_email, recipient_list = mock_send_mail.call_args[0]

        self.assertIn("123", subject)
        self.assertIn("123", message)
        self.assertEqual(from_email, "from@example.com")
        self.assertEqual(recipient_list, ["user@example.com"])

    @override_settings(
        TWILIO_ACCOUNT_SID="sid",
        TWILIO_AUTH_TOKEN="token",
        TWILIO_FROM_NUMBER="+10000000000",
    )
    @patch("orders.tasks.Client")
    def test_send_order_status_sms_sends_message(self, mock_client):
        instance = mock_client.return_value

        send_order_status_sms(456, "shipped", "+19999999999")

        instance.messages.create.assert_called_once()
        kwargs = instance.messages.create.call_args.kwargs
        self.assertIn("456", kwargs["body"])
        self.assertEqual(kwargs["to"], "+19999999999")

    @patch("orders.tasks.Client")
    def test_send_order_status_sms_missing_credentials_no_call(self, mock_client):
        send_order_status_sms(789, "processing", "+19999999999")

        mock_client.assert_not_called()

@override_settings(ORDER_PENDING_TIMEOUT_MINUTES=30, SECURE_SSL_REDIRECT=False)
class AutoCancelStaleOrdersTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="pendinguser",
            email="pending@example.com",
            password="pass",  # nosec B106
        )
        self.category = Category.objects.create(name="Accessories")
        self.product = Product.objects.create(
            product_name="Cable",
            price=10,
            inventory=5,
            category=self.category,
        )

    def test_cancels_stale_pending_orders_and_restores_inventory(self):
        order = Order.objects.create(
            user=self.user,
            total_price=20,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.product_name,
            quantity=2,
            unit_price=self.product.price,
        )
        self.product.inventory = 3
        self.product.save(update_fields=["inventory"])

        order.created_at = timezone.now() - timedelta(minutes=45)
        order.save(update_fields=["created_at"])

        with self.captureOnCommitCallbacks(execute=True):
            canceled = auto_cancel_stale_pending_orders()

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(canceled, 1)
        self.assertEqual(order.status, Order.Status.CANCELED)
        self.assertEqual(self.product.inventory, 5)

    def test_recent_pending_order_not_canceled(self):
        order = Order.objects.create(
            user=self.user,
            total_price=10,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.product_name,
            quantity=1,
            unit_price=self.product.price,
        )

        with self.captureOnCommitCallbacks(execute=True):
            canceled = auto_cancel_stale_pending_orders()

        order.refresh_from_db()
        self.assertEqual(canceled, 0)
        self.assertEqual(order.status, Order.Status.PENDING)

