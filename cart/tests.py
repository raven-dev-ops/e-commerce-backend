# cart/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product
from .models import Cart, CartItem

User = get_user_model()

class CartModelTest(TestCase):
    def setUp(self):
        Product.drop_collection()
        Cart.drop_collection()
        CartItem.drop_collection()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.product = Product.objects.create(_id="prod3", product_name='Test Product', price=10.00)
        self.cart = Cart.objects.create(user_id=str(self.user.id))

    def test_cart_creation(self):
        self.assertEqual(str(self.cart), f"Cart {self.cart.id} for user {self.user.id}")

    def test_cart_item_creation(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(str(item), f"2 x {self.product.product_name}")
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product, self.product)
