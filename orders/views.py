# orders/views.py

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import datetime
import stripe

from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product
from authentication.models import Address
from .serializers import OrderSerializer

import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")  # Replace with your actual Stripe secret key (use env variable in production!)

class OrderViewSet(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user

        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')

        # Fetch default addresses or use provided IDs
        shipping_address = Address.objects(user=user.id, is_default_shipping=True).first()
        billing_address = Address.objects(user=user.id, is_default_billing=True).first()

        if shipping_address_id:
            shipping_address = get_object_or_404(Address, id=shipping_address_id, user=user.id)
        if billing_address_id:
            billing_address = get_object_or_404(Address, id=billing_address_id, user=user.id)

        if not shipping_address:
            return Response({"detail": "Shipping address is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not billing_address:
            return Response({"detail": "Billing address is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user's cart
        cart = Cart.objects(user_id=str(user.id)).first()
        if not cart or not getattr(cart, "items", []):
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order_items = []
        subtotal = 0

        for item in getattr(cart, "items", []):
            try:
                product = Product.objects.get(id=item.product_id)
            except Product.DoesNotExist:
                return Response({"detail": f"Product with ID {item.product_id} not found."},
                                status=status.HTTP_404_NOT_FOUND)
            order_item = OrderItem(
                product_id=str(product.id),
                quantity=item.quantity
            )
            order_items.append(order_item)
            subtotal += product.price * item.quantity

        # Shipping and tax logic (example: flat rates)
        shipping_cost = 5.00
        tax_rate = 0.08

        discount_amount = 0
        discount_details = None
        if getattr(cart, "discount", None):
            discount = cart.discount
            discount_details = {
                'code': discount.code,
                'type': discount.discount_type,
                'value': discount.value,
                'amount': 0
            }
            if discount.discount_type == 'percentage':
                discount_amount = (subtotal * discount.value) / 100
                discount_amount = min(discount_amount, subtotal)
            elif discount.discount_type == 'fixed':
                discount_amount = min(discount.value, subtotal)
            discount_details['amount'] = round(discount_amount, 2)
            subtotal -= discount_amount

            if getattr(discount, "times_used", None) is not None:
                discount.times_used += 1

        tax_amount = round(subtotal * tax_rate, 2)
        total_price = subtotal + shipping_cost + tax_amount

        payment_method_id = request.data.get('payment_method_id')
        if not payment_method_id:
            return Response({"detail": "Payment method ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),  # Stripe expects amount in cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata={'user_id': str(user.id)}
            )
        except stripe.error.CardError as e:
            return Response({"detail": f"Payment failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Payment processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Payment succeeded, create the Order
        order = Order(
            user=user.id,
            created_at=datetime.utcnow(),
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_price=total_price,
            discount_code=discount_details['code'] if discount_details else None,
            discount_type=discount_details['type'] if discount_details else None,
            discount_amount=round(discount_amount, 2) if discount_amount else 0,
            items=order_items,
            status='processing'
        )
        order.save()

        # Save discount increment
        if getattr(cart, "discount", None):
            cart.discount.save()

        # Clear cart
        cart.items = []
        cart.discount = None
        cart.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
