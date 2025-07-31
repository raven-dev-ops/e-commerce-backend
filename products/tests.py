# products/tests.py

from django.test import TestCase
from mongoengine import connect, disconnect
import mongomock
from products.models import Product
from products.serializers import ProductSerializer

class ProductModelSerializerTest(TestCase):
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
            review_count=10
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Soap")

    def test_product_serializer(self):
        serializer = ProductSerializer(instance=self.product)
        data = serializer.data
        self.assertEqual(data['product_name'], "Test Soap")
        self.assertEqual(data['price'], '9.99')  # Decimal serialized as string
        self.assertIn("bath", [tag.lower() for tag in data['tags']])
        self.assertEqual(data['average_rating'], 4.5)
        self.assertEqual(data['review_count'], 10)
