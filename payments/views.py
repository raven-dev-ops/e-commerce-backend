# payments/views.py

import logging
import stripe
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from orders.models import Order  # Assuming your Order model is here

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle Stripe event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent['id'])
            order.status = Order.Status.PROCESSING
            order.save()
            logger.info('Order %s status updated to Processing', order.id)
        except Order.DoesNotExist:
            logger.warning(
                'Order with payment_intent_id %s not found', payment_intent["id"]
            )

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        try:
            order = Order.objects.get(payment_intent_id=payment_intent['id'])
            order.status = Order.Status.FAILED
            order.save()
            logger.info('Order %s status updated to Payment Failed', order.id)
        except Order.DoesNotExist:
            logger.warning(
                'Order with payment_intent_id %s not found', payment_intent["id"]
            )

    return HttpResponse(status=200)
