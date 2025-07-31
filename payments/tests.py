from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Payment, Transaction


class PaymentsModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="john", password="pass")

        self.payment = Payment.objects.create(
            user=self.user,
            invoice="INV1001",
            amount=Decimal("150.00"),
            method="CC",
        )

        self.transaction = Transaction.objects.create(
            payment=self.payment,
            status="Completed",
        )

    def test_payment_str(self):
        self.assertEqual(str(self.payment), f"Payment {self.payment.id} - john - 150.00")

    def test_transaction_str(self):
        self.assertIn("Transaction", str(self.transaction))
        self.assertIn("Completed", str(self.transaction))
