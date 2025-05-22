import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from orders.models import Order  # Assuming your Order model is in orders.models

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', None)
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET  # You will add this to settings.py

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        print('PaymentIntent was successful!') # Basic logging
        payment_intent = event['data']['object']
        # Find the corresponding order and update its status
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.status = 'Processing'  # Or a suitable status like 'Processing' or 'Completed'
            order.save()
            print(f'Order {order.id} status updated to Processing')
        except Order.DoesNotExist:
            print(f'Order with payment_intent_id {payment_intent.id} not found')
    elif event['type'] == 'payment_intent.payment_failed':
        print('PaymentIntent failed!') # Basic logging
        payment_intent = event['data']['object']
        # Find the corresponding order and update its status
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.status = 'Payment Failed' # Or a suitable status
            order.save()
            print(f'Order {order.id} status updated to Payment Failed')
        except Order.DoesNotExist:
            print(f'Order with payment_intent_id {payment_intent.id} not found')
    # ... handle other event types
