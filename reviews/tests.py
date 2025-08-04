# reviews/tests.py

from django.test import TestCase, override_settings
from django.urls import reverse
from mongoengine import connect, disconnect
import mongomock
from reviews.models import Review
from products.models import Product
from django.contrib.auth import get_user_model
from reviews.serializers import ReviewSerializer
from rest_framework.test import APIClient
from datetime import datetime

User = get_user_model()


class ReviewModelSerializerTest(TestCase):
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
        Review.drop_collection()
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="password")
        # Create a test product
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439013",
            product_name="Test Product",
            category="Test Category",
            description="Test description",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        # Create a review instance
        self.review = Review.objects.create(
            user_id=self.user.pk,
            product=self.product,
            rating=4,
            comment="Great product!",
            status="approved",
            created_at=datetime.utcnow(),
        )

    def test_review_str(self):
        self.assertEqual(str(self.review.product), "Test Product")

    def test_review_user_property(self):
        self.assertEqual(self.review.user.username, "testuser")

    def test_review_serializer(self):
        serializer = ReviewSerializer(instance=self.review)
        data = serializer.data
        self.assertEqual(data["user"], "testuser")
        self.assertEqual(data["rating"], 4)
        self.assertEqual(data["comment"], "Great product!")
        self.assertEqual(data["status"], "approved")


@override_settings(SECURE_SSL_REDIRECT=False)
class ReviewAPIPaginationTest(TestCase):
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
        Review.drop_collection()
        self.user = User.objects.create_user(username="apiuser", password="password")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439014",
            product_name="Test Product",
            category="Test Category",
            description="Test description",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        for i in range(15):
            Review.objects.create(
                user_id=self.user.pk,
                product=self.product,
                rating=5,
                comment=f"Review {i}",
                status="approved",
                created_at=datetime.utcnow(),
            )

    def test_review_list_is_paginated(self):
        url = reverse("review-list")
        response = self.client.get(url, {"product_id": str(self.product.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

        response = self.client.get(url, {"product_id": str(self.product.id), "page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)
