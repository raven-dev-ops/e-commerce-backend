from django.contrib.auth import get_user_model
from django.test import TestCase

from orders.models import Order, OrderItem


class OrderModelTestCase(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="orderuser", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=10,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

    def test_str_representation(self):
        text = str(self.order)
        self.assertIn(str(self.order.id), text)
        self.assertIn(self.user.username, text)

    def test_soft_delete_and_restore(self):
        order_id = self.order.id
        self.order.delete()

        self.assertFalse(Order.objects.filter(id=order_id).exists())
        self.assertTrue(Order.all_objects.filter(id=order_id).exists())

        deleted = Order.all_objects.get(id=order_id)
        self.assertTrue(deleted.is_deleted)

        deleted.restore()
        self.assertTrue(Order.objects.filter(id=order_id).exists())

    def test_active_manager_excludes_deleted(self):
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username="otheruser", password="pass"  # nosec B106
        )
        other_order = Order.objects.create(
            user=other_user,
            total_price=5,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

        other_order.delete()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.all_objects.count(), 2)


class OrderItemModelTestCase(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="itemuser", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=20,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product_name="Test Product",
            quantity=2,
            unit_price=10,
        )

    def test_order_item_str(self):
        self.assertEqual(str(self.item), "Test Product (x2)")

