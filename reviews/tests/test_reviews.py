# reviews/tests.py

from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from reviews.models import Review
from products.models import Product
from backend.serializers.reviews import ReviewSerializer
from backend.tests.utils import MongoTestCase

User = get_user_model()


class ReviewModelSerializerTest(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        Review.drop_collection()
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )  # nosec B106
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
class ReviewAPIPaginationTest(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        Review.drop_collection()
        self.user = User.objects.create_user(
            username="apiuser", password="password"
        )  # nosec B106
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
        url = reverse("review-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"product_id": str(self.product.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

        response = self.client.get(url, {"product_id": str(self.product.id), "page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ReviewCreationThrottleTest(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        Review.drop_collection()
        cache.clear()
        self.user = User.objects.create_user(
            username="throttleuser", password="password"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_review_creation_is_throttled(self):
        url = reverse("review-list", kwargs={"version": "v1"})

        for i in range(5):
            product = Product.objects.create(
                _id=f"prod{i}",
                product_name=f"Product {i}",
                category="Test Category",
                description="Test description",
                price=9.99,
                ingredients=[],
                benefits=[],
                tags=[],
                inventory=10,
                reserved_inventory=0,
            )
            response = self.client.post(
                url, {"product_id": product.id, "rating": 5}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        product = Product.objects.create(
            _id="prod-final",
            product_name="Product final",
            category="Test Category",
            description="Test description",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        response = self.client.post(
            url, {"product_id": product.id, "rating": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ReviewRatingRecalculationTest(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        Review.drop_collection()
        cache.clear()
        self.user = User.objects.create_user(
            username="ratinguser", password="password"
        )  # nosec B106
        self.admin = User.objects.create_user(
            username="admin", password="password", is_staff=True
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.product = Product.objects.create(
            _id="prod-rating",
            product_name="Rating Product",
            category="Test Category",
            description="Test description",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )

    def test_review_creation_updates_product_rating(self):
        url = reverse("review-list", kwargs={"version": "v1"})
        response = self.client.post(
            url, {"product_id": str(self.product.id), "rating": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.reload()
        self.assertEqual(self.product.review_count, 1)
        self.assertEqual(self.product.approved_review_count, 0)
        self.assertEqual(self.product.average_rating, 0)

        review_id = response.data["id"]
        moderate_url = reverse(
            "review-moderate", kwargs={"pk": review_id, "version": "v1"}
        )
        response = self.admin_client.post(
            moderate_url, {"status": "approved"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.reload()
        self.assertEqual(self.product.review_count, 1)
        self.assertEqual(self.product.approved_review_count, 1)
        self.assertEqual(self.product.average_rating, 5)

    def test_review_update_recalculates_product_rating(self):
        url = reverse("review-list", kwargs={"version": "v1"})
        response = self.client.post(
            url, {"product_id": str(self.product.id), "rating": 4}, format="json"
        )
        review_id = response.data["id"]
        self.admin_client.post(
            reverse("review-moderate", kwargs={"pk": review_id, "version": "v1"}),
            {"status": "approved"},
            format="json",
        )
        self.product.reload()
        self.assertEqual(self.product.average_rating, 4)

        update_url = reverse("review-detail", kwargs={"pk": review_id, "version": "v1"})
        response = self.client.put(update_url, {"rating": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.reload()
        self.assertEqual(self.product.average_rating, 2)
        self.assertEqual(self.product.approved_review_count, 1)
        self.assertEqual(self.product.review_count, 1)

    def test_review_deletion_updates_product_rating(self):
        url = reverse("review-list", kwargs={"version": "v1"})
        response = self.client.post(
            url, {"product_id": str(self.product.id), "rating": 3}, format="json"
        )
        review_id = response.data["id"]
        self.admin_client.post(
            reverse("review-moderate", kwargs={"pk": review_id, "version": "v1"}),
            {"status": "approved"},
            format="json",
        )
        self.product.reload()
        self.assertEqual(self.product.average_rating, 3)
        delete_url = reverse("review-detail", kwargs={"pk": review_id, "version": "v1"})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.product.reload()
        self.assertEqual(self.product.review_count, 0)
        self.assertEqual(self.product.approved_review_count, 0)
        self.assertEqual(self.product.average_rating, 0)
