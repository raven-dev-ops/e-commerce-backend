# reviews/tests.py

from django.test import TestCase
from mongoengine import connect, disconnect
import mongomock
from reviews.models import Review
from products.models import Product
from django.contrib.auth import get_user_model
from reviews.serializers import ReviewSerializer
from datetime import datetime

User = get_user_model()


class ReviewModelSerializerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
