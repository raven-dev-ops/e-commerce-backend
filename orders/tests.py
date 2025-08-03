# orders/tests.py

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from unittest.mock import patch
from orders.tasks import send_order_confirmation_email

class OrderModelTestCase(TestCase):
    
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.order = Order.objects.create(
            user=self.user,
            total_price=100.0,
            shipping_cost=10.0,
            tax_amount=5.0,
            status='pending'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_name="Widget",
            quantity=2,
            unit_price=50.0,
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first().product_name, "Widget")
        self.assertEqual(self.order.status, 'pending')


class OrderTasksTestCase(TestCase):

    @override_settings(DEFAULT_FROM_EMAIL='from@example.com')
    @patch('orders.tasks.send_mail')
    def test_send_order_confirmation_email(self, mock_send_mail):
        send_order_confirmation_email(1, 'user@example.com')
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[0]
        self.assertIn('Order Confirmation #1', args[0])
        self.assertIn('Thank you for your order', args[1])
        self.assertEqual(args[2], 'from@example.com')
        self.assertEqual(args[3], ['user@example.com'])
