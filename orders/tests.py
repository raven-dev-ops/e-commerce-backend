# orders/tests.py

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from unittest.mock import patch, MagicMock
from orders.tasks import send_order_confirmation_email
from products.models import Product
from cart.models import Cart
from discounts.models import Discount
from authentication.models import Address
from rest_framework.test import APIClient
from django.urls import reverse
from types import SimpleNamespace
import stripe
from mongoengine import connect, disconnect
import mongomock

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


class DummyCart:
    def __init__(self, items, discount=None):
        self.items = items
        self.discount = discount

    def save(self):
        pass


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderIntegrationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connect('mongoenginetest', host='mongodb://localhost', mongo_client_class=mongomock.MongoClient)

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        Product.drop_collection()
        Discount.drop_collection()
        Cart.drop_collection()
        User = get_user_model()
        self.user = User.objects.create_user(username='orderuser', password='pass')
        self.address = Address.objects.create(
            user=self.user,
            street='123 St',
            city='Town',
            country='Country',
            zip_code='12345',
            is_default_shipping=True,
            is_default_billing=True,
        )
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439013",
            product_name='Soap',
            category='Bath',
            price=10.0,
            inventory=5,
            reserved_inventory=0,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch('orders.views.send_order_confirmation_email.delay')
    @patch('orders.views.stripe.PaymentIntent.create')
    def test_create_order_success(self, mock_intent, mock_email):
        mock_intent.return_value = SimpleNamespace(id='pi_123')
        cart = DummyCart(items=[SimpleNamespace(product_id=str(self.product._id), quantity=2)])
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch('orders.views.Cart.objects', return_value=cart_qs), \
             patch('orders.views.Product.objects', product_qs), \
             patch('orders.views.OrderSerializer', serializer_mock):
            url = reverse('order-list')
            response = self.client.post(url, {'payment_method_id': 'pm_1'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertAlmostEqual(float(order.total_price), 26.6, places=2)

    @patch('orders.views.send_order_confirmation_email.delay')
    @patch('orders.views.stripe.PaymentIntent.create')
    def test_create_order_with_discount(self, mock_intent, mock_email):
        mock_intent.return_value = SimpleNamespace(id='pi_123')
        discount = Discount.objects.create(code='SAVE10', discount_type='percentage', value=10)
        cart = DummyCart(items=[SimpleNamespace(product_id=str(self.product._id), quantity=2)], discount=discount)
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch('orders.views.Cart.objects', return_value=cart_qs), \
             patch('orders.views.Product.objects', product_qs), \
             patch('orders.views.OrderSerializer', serializer_mock):
            url = reverse('order-list')
            response = self.client.post(url, {'payment_method_id': 'pm_1'}, format='json')
        self.assertEqual(response.status_code, 201)
        order = Order.objects.first()
        self.assertEqual(order.discount_code, 'SAVE10')
        self.assertAlmostEqual(order.discount_amount, 2.0, places=2)

    @patch('orders.views.stripe.PaymentIntent.create')
    def test_create_order_out_of_stock(self, mock_intent):
        cart = DummyCart(items=[SimpleNamespace(product_id=str(self.product._id), quantity=10)])
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch('orders.views.Cart.objects', return_value=cart_qs), \
             patch('orders.views.Product.objects', product_qs), \
             patch('orders.views.OrderSerializer', serializer_mock):
            url = reverse('order-list')
            response = self.client.post(url, {'payment_method_id': 'pm_1'}, format='json')
        self.assertEqual(response.status_code, 400)
        mock_intent.assert_not_called()

    @patch('orders.views.send_order_confirmation_email.delay')
    @patch('orders.views.stripe.PaymentIntent.create')
    def test_create_order_payment_failure(self, mock_intent, mock_email):
        mock_intent.side_effect = stripe.error.CardError(message="declined", param=None, code="card_declined")
        cart = DummyCart(items=[SimpleNamespace(product_id=str(self.product._id), quantity=1)])
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch('orders.views.Cart.objects', return_value=cart_qs), \
             patch('orders.views.Product.objects', product_qs), \
             patch('orders.views.OrderSerializer', serializer_mock):
            url = reverse('order-list')
            response = self.client.post(url, {'payment_method_id': 'pm_1'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
