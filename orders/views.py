# orders/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import stripe, os

from cart.models import Cart  # MongoEngine
from orders.models import Order, OrderItem  # Django ORM
from products.models import Product  # Django ORM
from authentication.models import Address  # Django ORM
from .serializers import OrderSerializer

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class OrderViewSet(viewsets.ViewSet):
    """
    Order endpoints (list, retrieve, create) using Django ORM.
    Cart is always read from MongoDB via MongoEngine.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all orders for current user."""
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a specific order by ID (must belong to user)."""
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def create(self, request):
        """Checkout: Create an order from user's cart."""
        user = request.user

        # Addresses
        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')
        shipping_address = Address.objects.filter(user=user, is_default_shipping=True).first()
        billing_address = Address.objects.filter(user=user, is_default_billing=True).first()
        if shipping_address_id:
            shipping_address = get_object_or_404(Address, id=shipping_address_id, user=user)
        if billing_address_id:
            billing_address = get_object_or_404(Address, id=billing_address_id, user=user)
        if not shipping_address:
            return Response({"detail": "Shipping address required."}, status=400)
        if not billing_address:
            return Response({"detail": "Billing address required."}, status=400)

        # MongoEngine Cart
        cart = Cart.objects(user_id=str(user.id)).first()
        if not cart or not getattr(cart, "items", []):
            return Response({"detail": "Cart is empty."}, status=400)

        subtotal = 0
        order_items = []

        for item in cart.items:
            try:
                product = Product.objects.get(id=item.product_id)
            except Product.DoesNotExist:
                return Response({"detail": f"Product ID {item.product_id} not found."}, status=404)
            subtotal += product.price * item.quantity
            order_items.append({
                "product_name": product.name,
                "quantity": item.quantity,
                "unit_price": product.price,
            })

        # Shipping, tax, discounts (simplified)
        shipping_cost = 5.0
        tax_amount = round(subtotal * 0.08, 2)
        total_price = subtotal + shipping_cost + tax_amount
        discount_code = None
        discount_type = None
        discount_value = None
        discount_amount = 0

        # Apply discount if present
        if getattr(cart, "discount", None):
            discount = cart.discount
            discount_code = discount.code
            discount_type = discount.discount_type
            discount_value = discount.value
            if discount.discount_type == 'percentage':
                discount_amount = round(subtotal * discount.value / 100, 2)
            elif discount.discount_type == 'fixed':
                discount_amount = min(discount.value, subtotal)
            subtotal -= discount_amount
            total_price = subtotal + shipping_cost + tax_amount

        # Stripe Payment
        payment_method_id = request.data.get('payment_method_id')
        if not payment_method_id:
            return Response({"detail": "Payment method required."}, status=400)
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),  # cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata={'user_id': str(user.id)}
            )
        except stripe.error.CardError as e:
            return Response({"detail": f"Payment failed: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"detail": f"Payment error: {str(e)}"}, status=500)

        # Create order (Django ORM)
        order = Order.objects.create(
            user=user,
            created_at=timezone.now(),
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_price=total_price,
            payment_intent_id=intent.id,
            status='processing',
            discount_code=discount_code,
            discount_type=discount_type,
            discount_value=discount_value,
            discount_amount=discount_amount,
        )
        # Save OrderItems
        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item) for item in order_items
        ])

        # Optional: Increment discount times_used
        if getattr(cart, "discount", None):
            if hasattr(cart.discount, "times_used"):
                cart.discount.times_used += 1
                cart.discount.save()

        # Clear cart
        cart.items = []
        cart.discount = None
        cart.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
