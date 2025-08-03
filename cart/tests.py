# cart/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from mongoengine import connect, disconnect
import mongomock
from products.models import Product
from .models import Cart, CartItem

User = get_user_model()

class CartModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connect('mongoenginetest', host='mongodb://localhost', mongo_client_class=mongomock.MongoClient)

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        Cart.drop_collection()
        Product.drop_collection()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439012",
            product_name='Test Product',
            category='Test',
            price=10.00,
        )
        self.cart = Cart.objects.create(user_id=str(self.user.id))

    def test_cart_creation(self):
        self.assertEqual(str(self.cart), f"Cart {self.cart.id} for user {self.user.id}")

    def test_cart_item_creation(self):
        item = CartItem.objects.create(cart=self.cart, product_id=str(self.product.id), quantity=2)
        self.assertEqual(str(item), f"2 x {self.product.id}")
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product_id, str(self.product.id))
