from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import stripe
from secrets import token_hex

from orders.models import Order, OrderItem
from orders.tasks import send_order_confirmation_email
from orders.services import create_order_from_cart
from products.models import Product
from cart.models import Cart
from discounts.models import Discount
from authentication.models import Address
from backend.tests.utils import MongoTestCase


class OrderModelTestCase(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser", password="pass"
        )  # nosec B106
        self.order = Order.objects.create(
            user=self.user,
            total_price=100.0,
            shipping_cost=10.0,
            tax_amount=5.0,
            status="pending",
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_name="Widget",
            quantity=2,
            unit_price=50.0,
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first().product_name, "Widget")
        self.assertEqual(self.order.status, "pending")

    def test_soft_delete_and_restore_order(self):
        order_id = self.order.id
        self.order.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())
        deleted = Order.all_objects.get(id=order_id)
        self.assertTrue(deleted.is_deleted)
        deleted.restore()
        self.assertTrue(Order.objects.filter(id=order_id).exists())


class OrderTasksTestCase(TestCase):

    @override_settings(DEFAULT_FROM_EMAIL="from@example.com")
    @patch("orders.tasks.send_mail")
    def test_send_order_confirmation_email(self, mock_send_mail):
        send_order_confirmation_email(1, "user@example.com")
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[0]
        self.assertIn("Order Confirmation #1", args[0])
        self.assertIn("Thank you for your order", args[1])
        self.assertEqual(args[2], "from@example.com")
        self.assertEqual(args[3], ["user@example.com"])


class OrderStatusSMSTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="smsuser", password="pass", phone_number="+1234567890"
        )  # nosec B106
        self.order = Order.objects.create(
            user=self.user,
            total_price=10.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

    @patch("orders.tasks.send_order_status_sms.delay")
    def test_status_change_triggers_sms(self, mock_delay):
        self.order.status = Order.Status.SHIPPED
        self.order.save()
        mock_delay.assert_called_once_with(
            self.order.id, Order.Status.SHIPPED, "+1234567890"
        )


class OrderStatusWebSocketTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="wsuser", password="pass"
        )  # nosec B106
        self.order = Order.objects.create(
            user=self.user,
            total_price=10.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

    @patch("orders.models.async_to_sync")
    @patch("orders.models.get_channel_layer")
    def test_status_change_sends_ws_notification(
        self, mock_get_channel_layer, mock_async_to_sync
    ):
        channel_layer = MagicMock()
        mock_get_channel_layer.return_value = channel_layer
        send_mock = MagicMock()
        mock_async_to_sync.return_value = send_mock

        self.order.status = Order.Status.SHIPPED
        self.order.save()

        mock_async_to_sync.assert_called_once_with(channel_layer.group_send)
        send_mock.assert_called_once_with(
            f"order_{self.order.id}",
            {"type": "status.update", "status": Order.Status.SHIPPED},
        )


class DummyCart:
    def __init__(self, items, discount=None):
        self.items = items
        self.discount = discount

    def save(self):
        pass


class CreateOrderFromCartTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="serviceuser", password="pass"
        )  # nosec B106
        Address.objects.create(
            user=self.user,
            street="123 St",
            city="Town",
            country="Country",
            zip_code="12345",
            is_default_shipping=True,
            is_default_billing=True,
        )
        self.product = SimpleNamespace(
            id="prod1",
            product_name="Soap",
            price=10.0,
            inventory=5,
            reserved_inventory=0,
        )
        self.cart_items = [SimpleNamespace(product_id=self.product.id, quantity=2)]

        self.product_qs = MagicMock()
        self.product_qs.get.return_value = self.product

        def filter_mock(*args, **kwargs):
            class QS:
                def update(inner_self, **update_kwargs):
                    expr = update_kwargs["reserved_inventory"]
                    qty = getattr(getattr(expr, "rhs", None), "value", 0)
                    self.product.reserved_inventory += qty

            return QS()

        self.product_qs.filter.side_effect = filter_mock

    def _setup_cart(self, discount=None):
        cart = DummyCart(items=self.cart_items, discount=discount)
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        return cart_qs

    def test_applies_discount_and_updates_inventory(self):
        discount = SimpleNamespace(
            code="SAVE10",
            discount_type="percentage",
            value=10,
            times_used=0,
        )

        def save():
            pass

        discount.save = save

        cart_qs = self._setup_cart(discount)

        with (
            patch("orders.services.Cart.objects", return_value=cart_qs),
            patch("orders.services.Product.objects", self.product_qs),
            patch(
                "orders.services.get_or_create_user_ref",
                return_value=SimpleNamespace(id=self.user.id),
            ),
            patch(
                "orders.services.stripe.PaymentIntent.create",
                return_value=SimpleNamespace(id="pi_123"),
            ),
        ):
            order = create_order_from_cart(self.user, {"payment_method_id": "pm_1"})

        self.assertEqual(order.discount_code, "SAVE10")
        self.assertAlmostEqual(order.discount_amount, 2.0, places=2)
        self.assertEqual(discount.times_used, 1)
        self.assertEqual(self.product.reserved_inventory, 2)

    def test_updates_inventory_without_discount(self):
        cart_qs = self._setup_cart()

        with (
            patch("orders.services.Cart.objects", return_value=cart_qs),
            patch("orders.services.Product.objects", self.product_qs),
            patch(
                "orders.services.get_or_create_user_ref",
                return_value=SimpleNamespace(id=self.user.id),
            ),
            patch(
                "orders.services.stripe.PaymentIntent.create",
                return_value=SimpleNamespace(id="pi_123"),
            ),
        ):
            order = create_order_from_cart(self.user, {"payment_method_id": "pm_1"})

        self.assertIsNone(order.discount_code)
        self.assertEqual(self.product.reserved_inventory, 2)

    def test_creates_gift_order(self):
        cart_qs = self._setup_cart()

        with (
            patch("orders.services.Cart.objects", return_value=cart_qs),
            patch("orders.services.Product.objects", self.product_qs),
            patch(
                "orders.services.get_or_create_user_ref",
                return_value=SimpleNamespace(id=self.user.id),
            ),
            patch(
                "orders.services.stripe.PaymentIntent.create",
                return_value=SimpleNamespace(id="pi_123"),
            ),
        ):
            order = create_order_from_cart(
                self.user,
                {
                    "payment_method_id": "pm_1",
                    "is_gift": True,
                    "gift_message": "Happy Birthday!",
                },
            )

        self.assertTrue(order.is_gift)
        self.assertEqual(order.gift_message, "Happy Birthday!")


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderIntegrationTestCase(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        Discount.drop_collection()
        Cart.drop_collection()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="orderuser", password="pass"
        )  # nosec B106
        self.address = Address.objects.create(
            user=self.user,
            street="123 St",
            city="Town",
            country="Country",
            zip_code="12345",
            is_default_shipping=True,
            is_default_billing=True,
        )
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439013",
            product_name="Soap",
            category="Bath",
            price=10.0,
            inventory=5,
            reserved_inventory=0,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("orders.views.send_order_confirmation_email.delay")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_success(self, mock_intent, mock_email):
        mock_intent.return_value = SimpleNamespace(id="pi_123")
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=2)]
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url, {"payment_method_id": "pm_1"}, format="json"
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertAlmostEqual(float(order.total_price), 26.6, places=2)

    @patch("orders.views.send_order_confirmation_email.delay")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_with_discount(self, mock_intent, mock_email):
        mock_intent.return_value = SimpleNamespace(id="pi_123")
        discount = Discount.objects.create(
            code="SAVE10", discount_type="percentage", value=10
        )
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=2)],
            discount=discount,
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url, {"payment_method_id": "pm_1"}, format="json"
            )
        self.assertEqual(response.status_code, 201)
        order = Order.objects.first()
        self.assertEqual(order.discount_code, "SAVE10")
        self.assertAlmostEqual(order.discount_amount, 2.0, places=2)

    @patch("orders.views.send_order_confirmation_email.delay")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_with_gift_message(self, mock_intent, mock_email):
        mock_intent.return_value = SimpleNamespace(id="pi_123")
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=1)]
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url,
                {
                    "payment_method_id": "pm_1",
                    "is_gift": True,
                    "gift_message": "Congrats",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        order = Order.objects.first()
        self.assertTrue(order.is_gift)
        self.assertEqual(order.gift_message, "Congrats")

    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_out_of_stock(self, mock_intent):
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=10)]
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url, {"payment_method_id": "pm_1"}, format="json"
            )
        self.assertEqual(response.status_code, 400)
        mock_intent.assert_not_called()

    @patch("orders.views.send_order_confirmation_email.delay")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_payment_failure(self, mock_intent, mock_email):
        mock_intent.side_effect = stripe.error.CardError(
            message="declined", param=None, code="card_declined"
        )
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=1)]
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url, {"payment_method_id": "pm_1"}, format="json"
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    @patch("backend.currency.requests.get")
    @patch("orders.views.send_order_confirmation_email.delay")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_create_order_with_currency_conversion(
        self, mock_intent, mock_email, mock_get
    ):
        mock_intent.return_value = SimpleNamespace(id="pi_123")
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {"rates": {"EUR": 2.0}}
        cart = DummyCart(
            items=[SimpleNamespace(product_id=str(self.product._id), quantity=2)]
        )
        cart_qs = MagicMock()
        cart_qs.first.return_value = cart
        product_qs = MagicMock()
        product_qs.get.return_value = self.product
        serializer_mock = MagicMock()
        serializer_mock.return_value.data = {}
        with patch("orders.services.Cart.objects", return_value=cart_qs), patch(
            "orders.services.Product.objects", product_qs
        ), patch("orders.views.OrderSerializer", serializer_mock):
            url = reverse("order-list", kwargs={"version": "v1"})
            response = self.client.post(
                url,
                {"payment_method_id": "pm_1", "currency": "eur"},
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        order = Order.objects.first()
        self.assertEqual(order.currency, "eur")
        self.assertAlmostEqual(float(order.total_price), 53.2, places=2)
        args, kwargs = mock_intent.call_args
        self.assertEqual(kwargs["currency"], "eur")
        self.assertEqual(kwargs["amount"], int(order.total_price * 100))


@override_settings(SECURE_SSL_REDIRECT=False)
class OrderCancelReleaseInventoryTestCase(MongoTestCase):

    def setUp(self):
        Product.drop_collection()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="canceluser", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(
            _id="507f1f77bcf86cd799439200",
            product_name="Cancel Soap",
            category="Bath",
            price=5.0,
            inventory=5,
            reserved_inventory=2,
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=10.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PROCESSING,
        )
        OrderItem.objects.create(
            order=self.order,
            product_name=self.product.product_name,
            quantity=2,
            unit_price=5.0,
        )

    def test_cancel_order_releases_inventory(self):
        self.order.status = Order.Status.CANCELED
        self.order.save()
        product = Product.objects.get(pk=self.product.id)
        self.assertEqual(product.reserved_inventory, 0)

    def test_cancel_endpoint_releases_inventory(self):
        url = reverse("order-cancel", kwargs={"pk": self.order.id, "version": "v1"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(pk=self.product.id)
        self.assertEqual(product.reserved_inventory, 0)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELED)

    def test_other_user_cannot_cancel_order(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="pass"  # nosec B106
        )
        other_client = APIClient()
        other_client.force_authenticate(other_user)
        url = reverse("order-cancel", kwargs={"pk": self.order.id, "version": "v1"})
        response = other_client.post(url)
        # The view filters by user, so a different user should see 404
        self.assertEqual(response.status_code, 404)


class OrderInvoiceDownloadTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="pdfuser", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.order = Order.objects.create(
            user=self.user,
            total_price=20.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=self.order,
            product_name="Widget",
            quantity=1,
            unit_price=20.0,
        )

    def test_invoice_endpoint_returns_pdf(self):
        url = reverse("order-invoice", kwargs={"pk": self.order.id, "version": "v1"})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


WEBHOOK_SECRET = token_hex(16)
INVALID_WEBHOOK_SECRET = token_hex(16)


class ShipmentWebhookTestCase(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="webhookuser", password="pass"
        )  # nosec B106
        self.order = Order.objects.create(
            user=self.user,
            total_price=10.0,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )
        self.client = APIClient()
        self.url = reverse("shipment-webhook", kwargs={"version": "v1"})

    @override_settings(
        SHIPMENT_WEBHOOK_SECRET=WEBHOOK_SECRET,
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_updates_order_status(self):
        response = self.client.post(
            self.url,
            {"order_id": self.order.id, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN=WEBHOOK_SECRET,
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)

    @override_settings(
        SHIPMENT_WEBHOOK_SECRET=WEBHOOK_SECRET,
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_rejects_invalid_token(self):
        response = self.client.post(
            self.url,
            {"order_id": self.order.id, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN=INVALID_WEBHOOK_SECRET,
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(
        SHIPMENT_WEBHOOK_SECRET=WEBHOOK_SECRET,
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_missing_order_id_or_status_returns_400(self):
        base_kwargs = {"version": "v1"}
        # Missing order_id
        response = self.client.post(
            self.url, {"status": Order.Status.SHIPPED}, format="json", HTTP_X_WEBHOOK_TOKEN=WEBHOOK_SECRET
        )
        self.assertEqual(response.status_code, 400)
        # Missing status
        response = self.client.post(
            self.url, {"order_id": self.order.id}, format="json", HTTP_X_WEBHOOK_TOKEN=WEBHOOK_SECRET
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(
        SHIPMENT_WEBHOOK_SECRET=WEBHOOK_SECRET,
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_invalid_status_returns_400(self):
        response = self.client.post(
            self.url,
            {"order_id": self.order.id, "status": "NOT_A_STATUS"},
            format="json",
            HTTP_X_WEBHOOK_TOKEN=WEBHOOK_SECRET,
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(
        SHIPMENT_WEBHOOK_SECRET=WEBHOOK_SECRET,
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver"],
    )
    def test_order_not_found_returns_404(self):
        response = self.client.post(
            self.url,
            {"order_id": 999999, "status": Order.Status.SHIPPED},
            format="json",
            HTTP_X_WEBHOOK_TOKEN=WEBHOOK_SECRET,
        )
        self.assertEqual(response.status_code, 404)
