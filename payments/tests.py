from django.test import TestCase, RequestFactory
from unittest.mock import patch
from django.conf import settings
from django.urls import reverse
from datetime import datetime
import stripe
from payments.views import stripe_webhook_view  # Import the view
from orders.models import Order  # Assuming your Order model is here
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status

class StripeWebhookViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.webhook_url = reverse('stripe_webhook')  # Make sure this name matches your urls.py
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test_secret'  # Set a test webhook secret

    @patch('stripe.Webhook.construct_event')
    def test_payment_intent_succeeded_handles_order_status_update(self, mock_construct_event):
        """
        Test that a payment_intent.succeeded webhook updates the order status to Processing.
        """
        order = Order.objects.create(
            payment_intent_id='pi_test_123',
            status='pending',
            user_id=1,  # Assuming this is a foreign key to a User model
            total_price=10.00,
            created_at=datetime.now()
        )

        mock_event_data = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_test_123'}}
        }
        mock_construct_event.return_value = mock_event_data

        request = self.factory.post(
            self.webhook_url,
            data='{"some": "payload"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='a_valid_signature'
        )

        response = stripe_webhook_view(request)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Processing')

    def test_webhook_invalid_signature(self):
        """
        Test that a webhook with an invalid signature returns HTTP 400.
        """
        with patch('stripe.Webhook.construct_event') as mock_construct_event:
            mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "sig_header", "webhook_secret"
            )

            request = self.factory.post(
                self.webhook_url,
                data='{"some": "payload"}',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='an_invalid_signature'
            )
            response = stripe_webhook_view(request)
            self.assertEqual(response.status_code, 400)

    def test_webhook_missing_signature(self):
        """
        Test that a webhook with a missing signature returns HTTP 400.
        """
        request = self.factory.post(
            self.webhook_url,
            data='{"some": "payload"}',
            content_type='application/json'  # No signature header
        )
        response = stripe_webhook_view(request)
        self.assertEqual(response.status_code, 400)

    @patch('stripe.Webhook.construct_event')
    def test_payment_intent_payment_failed_handles_order_status_update(self, mock_construct_event):
        """
        Test that a payment_intent.payment_failed webhook updates the order status to 'Payment Failed'.
        """
        order = Order.objects.create(
            payment_intent_id='pi_test_failed_456',
            status='pending',
            user_id=1,
            total_price=10.00,
            created_at=datetime.now()
        )

        mock_event_data = {
            'type': 'payment_intent.payment_failed',
            'data': {'object': {'id': 'pi_test_failed_456'}}
        }
        mock_construct_event.return_value = mock_event_data

        request = self.factory.post(
            self.webhook_url,
            data='{"some": "payload"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='a_valid_signature'
        )
        response = stripe_webhook_view(request)

        order.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.status, 'Payment Failed')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_event_for_nonexistent_payment_intent(self, mock_construct_event):
        """
        Test that the webhook handles events for non-existent payment intents gracefully.
        """
        mock_event_data = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_nonexistent_789'}}
        }
        mock_construct_event.return_value = mock_event_data

        request = self.factory.post(
            self.webhook_url,
            data='{"some": "payload"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='a_valid_signature'
        )
        response = stripe_webhook_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(payment_intent_id='pi_nonexistent_789').count(), 0)


User = get_user_model()

class PaymentIntentCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.create_payment_intent_url = '/api/create-payment-intent/'  # Assuming your URL

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_successfully(self, mock_stripe_create):
        """
        Test creating a payment intent successfully.
        """
        # Mock the Stripe API call to create a PaymentIntent
        mock_stripe_create.return_value = {
            'id': 'pi_test_123',
            'client_secret': 'pi_test_123_secret_xyz',
            'amount': 2500,
            'currency': 'usd',
        }

        data = {'amount': 25.00, 'currency': 'usd'} # Or whatever data your view expects
        response = self.client.post(self.create_payment_intent_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('clientSecret', response.data)

    def test_create_payment_intent_invalid_data(self):
        """
        Test creating a payment intent with invalid data.
        """
        # Send request with missing required data (e.g., missing amount)
        invalid_data = {'currency': 'usd'}

        response = self.client.post(self.create_payment_intent_url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # You might want to check for specific error messages in the response data
        # For example, if your serializer returns an error for the missing field
        self.assertIn('amount', response.data) # Assert that 'amount' field has an error

class RefundTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='refunduser', password='refundpassword')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.refund_url = '/api/refund/'  # Assuming your refund URL
        self.paid_order = Order.objects.create(
            user=self.user,
            total_price=50.00,
            status='Processing',  # Assuming 'Processing' means paid after webhook
            payment_intent_id='pi_paid_for_refund', # Add a payment intent ID
            created_at=datetime.now()
        )

    @patch('stripe.Refund.create')
    def test_successful_refund(self, mock_stripe_refund_create):
        """
        Test initiating a successful refund.
        """
        # Mock the Stripe API call for creating a refund
        mock_stripe_refund_create.return_value = {
            'id': 're_test_123',
            'status': 'succeeded',
            'amount': 5000,
        }

        data = {'order_id': self.paid_order.id}
        response = self.client.post(self.refund_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.paid_order.refresh_from_db()
        self.assertEqual(self.paid_order.status, 'Refunded') # Assuming 'Refunded' is your status

    def test_refund_unpaid_order(self):
        """
        Test attempting to refund an unpaid order.
        """
        unpaid_order = Order.objects.create(user=self.user, total_price=20.00, status='pending', created_at=datetime.now())
        data = {'order_id': unpaid_order.id}
        response = self.client.post(self.refund_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refund_already_refunded_order(self):
        refunded_order = Order.objects.create(user=self.user, total_price=30.00, status='Refunded', created_at=datetime.now())
        data = {'order_id': refunded_order.id}
        response = self.client.post(self.refund_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refund_nonexistent_order(self):
        """
        Test attempting to refund a non-existent order.
        """
        nonexistent_order_id = 999  # Assuming this ID does not exist
        data = {'order_id': nonexistent_order_id}
        response = self.client.post(self.refund_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)