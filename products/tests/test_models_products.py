from django.test import TestCase

from products.models import Product
from backend.serializers.products import ProductSerializer
from backend.tests.utils import MongoTestCase


class ProductModelSerializerTest(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439011",
            product_name="Test Soap",
            category="Bath",
            description="A soothing soap",
            price=9.99,
            ingredients=["Sodium hydroxide", "Water", "Fragrance"],
            images=["http://example.com/image1.jpg"],
            variations=[{"color": "blue"}, {"size": "small"}],
            weight=0.25,
            dimensions="3x3x1",
            benefits=["Moisturizing", "Gentle"],
            scent_profile="Lavender",
            variants=[{"type": "bar"}, {"type": "liquid"}],
            tags=["soap", "bath"],
            availability=True,
            inventory=100,
            reserved_inventory=5,
            average_rating=4.5,
            review_count=10,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Soap")

    def test_product_serializer(self):
        serializer = ProductSerializer(instance=self.product)
        data = serializer.data
        self.assertEqual(data["product_name"], "Test Soap")
        self.assertEqual(data["slug"], "test-soap")
        self.assertEqual(data["price"], "9.99")
        self.assertIn("bath", [tag.lower() for tag in data["tags"]])
        self.assertEqual(data["average_rating"], 4.5)
        self.assertEqual(data["review_count"], 10)

    def test_product_slug_unique(self):
        second = Product.objects.create(
            _id="507f1f77bcf86cd799439012",
            product_name="Test Soap",
            category="Bath",
            description="Another soap",
            price=9.99,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=0,
        )
        self.assertNotEqual(self.product.slug, second.slug)

    def test_soft_delete_and_restore(self):
        product_id = self.product._id
        self.product.delete()
        self.assertIsNone(Product.objects(_id=product_id).first())
        deleted = Product.all_objects(_id=product_id).first()
        self.assertIsNotNone(deleted)
        self.assertTrue(deleted.is_deleted)
        deleted.restore()
        self.assertIsNotNone(Product.objects(_id=product_id).first())
