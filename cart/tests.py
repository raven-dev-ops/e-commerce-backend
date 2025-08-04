# cart/tests.py

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from mongoengine import connect, disconnect
import mongomock
from products.models import Product
from .models import Cart, CartItem
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch

User = get_user_model()


class CartModelTest(TestCase):
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
        Cart.drop_collection()
        Product.drop_collection()
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439012",
            product_name="Test Product",
            category="Test",
            price=10.00,
        )
        self.cart = Cart.objects.create(user_id=str(self.user.id))

    def test_cart_creation(self):
        self.assertEqual(str(self.cart), f"Cart {self.cart.id} for user {self.user.id}")

    def test_cart_item_creation(self):
        item = CartItem.objects.create(
            cart=self.cart, product_id=str(self.product.id), quantity=2
        )
        self.assertEqual(str(item), f"2 x {self.product.id}")
        self.assertEqual(item.cart, self.cart)
        self.assertEqual(item.product_id, str(self.product.id))


@override_settings(SECURE_SSL_REDIRECT=False)
class CartAPITestCase(TestCase):
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
        Cart.drop_collection()
        CartItem.drop_collection()
        Product.drop_collection()
        self.user = User.objects.create_user(username="apiuser", password="pass123")
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439099",
            product_name="API Product",
            category="Test",
            price=5.00,
        )
        self.cart = Cart.objects.create(user_id=str(self.user.id))
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("cart.views.CartItem.objects")
    @patch("cart.views.CartView.get_cart")
    def test_add_item_to_cart(self, mock_get_cart, mock_objects):
        mock_get_cart.return_value = self.cart
        cart_item = CartItem(
            cart=self.cart, product_id=str(self.product.id), quantity=1
        )
        mock_objects.get_or_create.return_value = (cart_item, True)
        url = reverse("cart")
        response = self.client.post(
            url, {"product_id": str(self.product._id), "quantity": 1}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["quantity"], 1)

    @patch("cart.views.CartView.get_cart")
    def test_add_item_missing_product_id(self, mock_get_cart):
        mock_get_cart.return_value = self.cart
        url = reverse("cart")
        response = self.client.post(url, {"quantity": 1}, format="json")
        self.assertEqual(response.status_code, 400)

    @patch("cart.views.CartItem.objects")
    @patch("cart.views.CartView.get_cart")
    def test_update_item_quantity(self, mock_get_cart, mock_objects):
        mock_get_cart.return_value = self.cart
        cart_item = CartItem(
            cart=self.cart, product_id=str(self.product.id), quantity=1
        )
        mock_objects.get.return_value = cart_item
        url = reverse("cart")
        response = self.client.put(
            url, {"product_id": str(self.product._id), "quantity": 3}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["quantity"], 3)

    @patch("cart.views.CartView.get_cart")
    def test_update_item_invalid_quantity(self, mock_get_cart):
        mock_get_cart.return_value = self.cart
        url = reverse("cart")
        response = self.client.put(
            url, {"product_id": str(self.product._id), "quantity": 0}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    @patch("cart.views.CartItem.objects")
    @patch("cart.views.CartView.get_cart")
    def test_delete_item(self, mock_get_cart, mock_objects):
        mock_get_cart.return_value = self.cart
        cart_item = CartItem(
            cart=self.cart, product_id=str(self.product.id), quantity=1
        )
        mock_objects.get.return_value = cart_item
        url = reverse("cart")
        response = self.client.delete(
            url, {"product_id": str(self.product._id)}, format="json"
        )
        self.assertEqual(response.status_code, 204)

    @patch("cart.views.CartItem.objects")
    @patch("cart.views.CartView.get_cart")
    def test_delete_nonexistent_item(self, mock_get_cart, mock_objects):
        mock_get_cart.return_value = self.cart
        mock_objects.get.side_effect = CartItem.DoesNotExist
        url = reverse("cart")
        response = self.client.delete(url, {"product_id": "bad"}, format="json")
        self.assertEqual(response.status_code, 404)
