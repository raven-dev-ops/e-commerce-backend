from django.test import TestCase, override_settings
from unittest.mock import patch

from orders.tasks import send_order_confirmation_email, send_order_status_sms


class OrderTasksTestCase(TestCase):
    @override_settings(DEFAULT_FROM_EMAIL="from@example.com")
    @patch("orders.tasks.send_mail")
    def test_send_order_confirmation_email_uses_send_mail(self, mock_send_mail):
        send_order_confirmation_email(123, "user@example.com")

        mock_send_mail.assert_called_once()
        subject, message, from_email, recipient_list = mock_send_mail.call_args[0]

        self.assertIn("123", subject)
        self.assertIn("123", message)
        self.assertEqual(from_email, "from@example.com")
        self.assertEqual(recipient_list, ["user@example.com"])

    @override_settings(
        TWILIO_ACCOUNT_SID="sid",
        TWILIO_AUTH_TOKEN="token",
        TWILIO_FROM_NUMBER="+10000000000",
    )
    @patch("orders.tasks.Client")
    def test_send_order_status_sms_sends_message(self, mock_client):
        instance = mock_client.return_value

        send_order_status_sms(456, "shipped", "+19999999999")

        instance.messages.create.assert_called_once()
        kwargs = instance.messages.create.call_args.kwargs
        self.assertIn("456", kwargs["body"])
        self.assertEqual(kwargs["to"], "+19999999999")

    @patch("orders.tasks.Client")
    def test_send_order_status_sms_missing_credentials_no_call(self, mock_client):
        send_order_status_sms(789, "processing", "+19999999999")

        mock_client.assert_not_called()

