# orders/tests.py

from django.test import TestCase
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()


class OrderModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='orderuser', password='pass')
        self.order = Order.objects.create(
            user=self.user,
            total_price=100.0,
            shipping_cost=10.0,
            tax_amount=5.0,
            status='pending'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_name="Test Product",
            quantity=2,
            unit_price=50.0
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first().product_name, "Test Product")
        self.assertEqual(self.order.status, 'pending')
