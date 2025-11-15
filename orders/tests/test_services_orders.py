from django.contrib.auth import get_user_model

from backend.tests.utils import MongoTestCase
from orders.models import Order, OrderItem
from orders.services import release_reserved_inventory, generate_invoice_pdf
from products.models import Product


class ReleaseReservedInventoryTestCase(MongoTestCase):
    def setUp(self):
        Product.drop_collection()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="orderinv", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=50,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        self.product = Product.objects.create(
            _id="inv1",
            product_name="Inventory Soap",
            category="Bath",
            description="desc",
            price=5.0,
            ingredients=[],
            benefits=[],
            tags=[],
            inventory=10,
            reserved_inventory=5,
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product_name=self.product.product_name,
            quantity=2,
            unit_price=5.0,
        )

    def test_release_reserved_inventory_reduces_reserved_count(self):
        release_reserved_inventory(self.order)
        updated = Product.objects.get(_id=self.product._id)
        self.assertEqual(updated.reserved_inventory, 3)

    def test_release_reserved_inventory_does_not_go_negative(self):
        self.product.reserved_inventory = 1
        self.product.save()
        self.item.quantity = 5
        self.item.save()

        release_reserved_inventory(self.order)
        updated = Product.objects.get(_id=self.product._id)
        self.assertEqual(updated.reserved_inventory, 0)

    def test_release_reserved_inventory_handles_missing_product(self):
        # Item with product name that does not exist should be ignored gracefully
        OrderItem.objects.create(
            order=self.order,
            product_name="Unknown Product",
            quantity=1,
            unit_price=1.0,
        )

        # Should not raise
        release_reserved_inventory(self.order)

    def test_generate_invoice_pdf_returns_bytes(self):
        pdf_bytes = generate_invoice_pdf(self.order)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

