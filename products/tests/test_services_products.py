from django.test import TestCase
from django.contrib.auth import get_user_model

from products.models import Product
from products.services import get_recommended_products
from orders.models import Order, OrderItem
from backend.tests.utils import MongoTestCase


class ProductRecommendationServiceTestCase(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="recuser", password="pass"  # nosec B106
        )
        Product.objects.create(
            _id="p1",
            product_name="Soap A",
            category="Bath",
            description="desc",
            price=1.0,
            average_rating=4.0,
        )
        Product.objects.create(
            _id="p2",
            product_name="Soap B",
            category="Bath",
            description="desc",
            price=1.0,
            average_rating=5.0,
        )
        Product.objects.create(
            _id="p3",
            product_name="Lotion C",
            category="Beauty",
            description="desc",
            price=1.0,
        )
        order = Order.objects.create(
            user=self.user,
            total_price=1.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order, product_name="Soap A", quantity=1, unit_price=1.0
        )

    def test_recommend_products_from_purchase_history(self):
        recommendations = get_recommended_products(self.user)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].product_name, "Soap B")

    def test_returns_empty_list_for_new_user(self):
        user_model = get_user_model()
        new_user = user_model.objects.create_user(
            username="newuser", password="pass"  # nosec B106
        )
        self.assertEqual(get_recommended_products(new_user), [])

