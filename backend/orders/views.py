from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime # Import datetime
from rest_framework.decorators import action

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django.conf import settings # Import settings
import logging # Import logging
from products.utils import send_low_stock_notification # Import low stock notification function
from discounts.models import Discount # Import Discount model
from discounts.models import Discount # Import Discount model
from authentication.models import Address
import stripe
from .models import Cart, CartItem, Order, OrderItem
from products.models import Product # Import Product model to validate product_id
from .serializers import CartSerializer, CartItemSerializer
from .serializers import OrderSerializer # Import OrderSerializer
# Create your views here.

logger = logging.getLogger(__name__) # Get logger instance

class CartViewSet(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        # Assuming user is authenticated and user ID is available in request.user.id
        # You might need to adjust this based on your authentication setup
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        cart, created = Cart.objects.get_or_create(user=user_id)

        # Calculate cart subtotal to check against discount conditions
        current_subtotal = 0
        cart_product_ids = set()
        cart_category_ids = set()  # Assuming Product model has a 'category' field
        for item in cart.items:
            try:
                product = Product.objects.get(id=item.product_id)
                current_subtotal += product.price * item.quantity
                cart_product_ids.add(str(product.id))
                # Assuming product has a category field that is a ReferenceField to Category
                if hasattr(product, 'category') and product.category:
                    cart_category_ids.add(str(product.category.id))
            except Product.DoesNotExist:
                # Handle case where product in cart doesn't exist anymore
                # Optionally remove this item from the cart or log a warning
                pass # For now, just skip this item

        # Find applicable automatic discounts
        now = datetime.now()
        automatic_discounts = Discount.objects.filter(
            is_automatic=True,
            is_active=True,
            valid_from__lte=now if 'valid_from' in Discount._fields else None,
            valid_to__gte=now if 'valid_to' in Discount._fields else None,
        ).exclude('times_used__gte', models_usage_limit=('usage_limit') if 'usage_limit' in Discount._fields else None)

        best_automatic_discount = None
        best_discount_amount = 0

        for discount in automatic_discounts:
            # Check if cart qualifies for this automatic discount
            if discount.min_purchase_amount is not None and current_subtotal < discount.min_purchase_amount:
                continue # Cart does not meet minimum purchase amount
            if discount.target_products and not any(str(prod.id) in cart_product_ids for prod in discount.target_products):
                continue # Cart does not contain target products
            if discount.target_categories and not any(str(cat.id) in cart_category_ids for cat in discount.target_categories):
                continue # Cart does not contain target categories

            # Calculate potential discount amount
            potential_discount_amount = self.calculate_discount_amount(discount, current_subtotal)

            if potential_discount_amount > best_discount_amount:
                best_discount_amount = potential_discount_amount
                best_automatic_discount = discount

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({"detail": "product_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: Validate if product_id exists in Product model
        try:
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check for available inventory (total - reserved)
        product = Product.objects.get(id=product_id) # Fetch product again to get current inventory/reserved
        available_inventory = product.inventory - product.reserved_inventory
        if available_inventory < quantity:
            return Response({"detail": f"Insufficient available stock for {product.name}. Available: {available_inventory}"}, status=status.HTTP_400_BAD_REQUEST)

        # Atomically increment reserved inventory
        Product.objects(id=product.id).update_one(inc__reserved_inventory=quantity)

        cart, created = Cart.objects.get_or_create(user=user_id)

        # Check if the item is already in the cart
        for item in cart.items:
            if str(item.product_id) == str(product_id):
                item.quantity += quantity
                break
        else:
            # Item not in cart, add new item
            cart_item = CartItem(product_id=product_id, quantity=quantity)
            cart.items.append(cart_item)

        cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def apply_discount(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        discount_code = request.data.get('discount_code')
        if not discount_code:
            return Response({"detail": "discount_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            discount = Discount.objects.get(code=discount_code, is_active=True)

            # Check valid date range
            now = datetime.now()
            if discount.valid_from and now < discount.valid_from:
                return Response({"detail": "Discount is not yet active."}, status=status.HTTP_400_BAD_REQUEST)
            if discount.valid_to and now > discount.valid_to:
                return Response({"detail": "Discount has expired."}, status=status.HTTP_400_BAD_REQUEST)

            # Check usage limit
            if discount.usage_limit is not None and discount.times_used >= discount.usage_limit:
                return Response({"detail": "Discount usage limit reached."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the user's cart to check against discount conditions
            cart, created = Cart.objects.get_or_create(user=user_id)

            # Calculate current cart subtotal to check against min_purchase_amount
            current_subtotal = 0
            cart_product_ids = set()
            cart_category_ids = set() # Assuming Product model has a 'category' field
            for item in cart.items:
                try:
                    product = Product.objects.get(id=item.product_id)
                    current_subtotal += product.price * item.quantity
                    cart_product_ids.add(str(product.id))
                    # Assuming product has a category field that is a ReferenceField to Category
                    if product.category:
                        cart_category_ids.add(str(product.category.id))
                except Product.DoesNotExist:
                    # Handle case where product in cart doesn't exist anymore
                    return Response({"detail": f"Product with ID {item.product_id} not found in cart."}, status=status.HTTP_404_NOT_FOUND)

            # Check minimum purchase amount
            if discount.min_purchase_amount is not None and current_subtotal < discount.min_purchase_amount:
                return Response({"detail": f"Minimum purchase of ${discount.min_purchase_amount:.2f} required."}, status=status.HTTP_400_BAD_REQUEST)

            # Check target products or categories
            if discount.target_products and not any(str(prod.id) in cart_product_ids for prod in discount.target_products):
                return Response({"detail": "Discount is not applicable to products in your cart."}, status=status.HTTP_400_BAD_REQUEST)
            if discount.target_categories and not any(str(cat.id) in cart_category_ids for cat in discount.target_categories):
                 return Response({"detail": "Discount is not applicable to categories in your cart."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply discount to the user's cart
            cart, created = Cart.objects.get_or_create(user=user_id)
            cart.discount = discount
            cart.save()

            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Discount.DoesNotExist:
            return Response({"detail": "Invalid or expired discount code."}, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user
        
        # Get chosen shipping and billing address IDs from request data
        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')

        shipping_address = None
        billing_address = None

        # If no shipping address ID is provided, use the default
        shipping_address = Address.objects.filter(user=user.id, is_default_shipping=True).first()
        
        # If no billing address ID is provided, use the default
        billing_address = Address.objects.filter(user=user.id, is_default_billing=True).first()


        cart = Cart.objects.filter(user=user.id).first()
        if not cart or not cart.items:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Assuming request data might contain payment details, but we'll add a placeholder
        payment_details = request.data.get('payment_details') # Example: dictionary with card info, etc.

        # Create OrderItems from CartItems
        order_items = []
        total_price = 0
        subtotal = 0

        for item in cart.items:
            # Fetch the product to get the current price and ensure it exists
            try:
                product = Product.objects.get(id=item.product_id)
            except Product.DoesNotExist:
                # Handle case where product in cart doesn't exist anymore
                return Response({"detail": f"Product with ID {item.product_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        if shipping_address_id:
            try:
                selected_shipping_address = Address.objects.get(id=shipping_address_id, user=user.id)
                shipping_address = selected_shipping_address
            except Address.DoesNotExist:
                return Response({"detail": "Shipping address not found or does not belong to the user."}, status=status.HTTP_400_BAD_REQUEST)
        elif not shipping_address:
             return Response({"detail": "Shipping address is required (either default or provided ID)."}, status=status.HTTP_400_BAD_REQUEST)


        # If billing address ID is provided, try to find and use that address
        if billing_address_id:
            try:
                selected_billing_address = Address.objects.get(id=billing_address_id, user=user.id)
                billing_address = selected_billing_address
            except Address.DoesNotExist:
                return Response({"detail": "Billing address not found or does not belong to the user."}, status=status.HTTP_400_BAD_REQUEST)
        elif not billing_address:
             return Response({"detail": "Billing address is required (either default or provided ID)."}, status=status.HTTP_400_BAD_REQUEST)

        # Create OrderItems from CartItems

        order_item = OrderItem(
                product=str(item.product_id),  # Store product_id as string
                quantity=item.quantity,
                price=product.price # Use the current product price
            )
        order_items.append(order_item)
        subtotal += product.price * item.quantity

        # Placeholder for shipping and tax calculation
        shipping_cost = 5.00  # Flat rate shipping
        tax_rate = 0.08  # 8% tax

        # Calculate total price including shipping and tax
        discount_amount = 0
        if cart.discount and cart.discount.is_free_shipping:
            shipping_cost = 0 # Apply free shipping if discount provides it

        discount_details = None
        if cart.discount:
            discount = cart.discount
            discount_details = {
                'code': discount.code,
                'type': discount.discount_type,
                'value': discount.value,
                'amount': 0 # Calculated discount amount
            }

            if discount.discount_type == 'percentage':
                discount_amount = (subtotal * discount.value) / 100
                # Ensure discount amount doesn't exceed subtotal
                discount_amount = min(discount_amount, subtotal)
            elif discount.discount_type == 'fixed':
                discount_amount = discount.value
                # Ensure discount amount doesn't exceed subtotal
                discount_amount = min(discount_amount, subtotal)
            discount_details['amount'] = round(discount_amount, 2)
            subtotal -= discount_amount
            discount.times_used += 1
            # Save the discount later after successful order


        tax_amount = round(subtotal * tax_rate, 2) # Calculate tax based on discounted subtotal
        total_price = subtotal + shipping_cost + tax_amount
        if discount_details:
            order.discount_code = discount_details['code']
            order.discount_type = discount_details['type']
        order.discount_amount = round(discount_amount, 2)

        # Stripe payment processing
        payment_method_id = request.data.get('payment_method_id')

        if not payment_method_id:
             return Response({"detail": "Payment method ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),
 # Stripe uses cents
                currency='usd',  # Or your currency
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
            )

            if intent.status != 'succeeded':
                 return Response({"detail": f"Payment failed: {intent.last_payment_error.message}"}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If payment is successful, save the discount's usage count
        if cart.discount:
            cart.discount.save()

        # Create the Order

        # Decrement product inventory
        for item in cart.items:
            product = Product.objects.get(id=item.product_id)
            Product.objects(id=product.id).update_one(dec__inventory=item.quantity)
            Product.objects(id=product.id).update_one(dec__reserved_inventory=item.quantity)

            # Check for low stock after decrementing
            updated_product = Product.objects.get(id=product.id) # Retrieve the updated product
            if updated_product.inventory <= settings.LOW_STOCK_THRESHOLD and updated_product.inventory > 0:
                send_low_stock_notification(updated_product.name, updated_product.id, updated_product.inventory)


        order = Order(user=user.id, items=order_items, total_price=total_price, shipping_cost=shipping_cost, tax_amount=tax_amount, shipping_address=shipping_address, billing_address=billing_address, discount_details=discount_details)
        order.save()

        # Clear the user's cart after creating the order
        cart.items = []
        cart.save()
        order.payment_intent_id = intent.id # Store the PaymentIntent ID
        order.status = 'processing' # Set status to processing after successful payment
        # Serialize the created order and return it
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        # Retrieve all orders for the authenticated user
        orders = Order.objects.filter(user=user.id)

        # Serialize the orders
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        if not user_id:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        product_id = request.data.get('product_id')

        cart = Cart.objects.filter(user=user_id).first()
        if not cart:
            return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

        # Remove the item from the cart
        initial_item_count = len(cart.items)
        cart.items = [item for item in cart.items if str(item.product_id) != str(product_id)]

        if len(cart.items) == initial_item_count:
            return Response({"detail": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)

        # Decrement reserved inventory for the removed item's quantity
        # Note: This assumes the request data for remove_item includes the product_id and the quantity removed.
        # If removing a single item instance regardless of quantity, you might need a different approach.
        # Here, we decrement reserved inventory by 1 as typically remove item removes one instance.
        Product.objects(id=product_id).update_one(dec__reserved_inventory=1)
        cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            order = Order.objects.get(id=pk)
            if order.user != user.id:
                raise PermissionDenied("You do not have permission to access this order.")
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied:
             return Response({"detail": "You do not have permission to access this order."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # You might want to add additional permission checks here, e.g., IsAdminUser
        # For now, we'll allow the user who owns the order to update status (not typical for e-commerce)
        # or you would restrict this endpoint to admin users.

        try:
            order = Order.objects.get(id=pk)
            # Optional: Check if order.user == user.id if only owner can update status

            new_status = request.data.get('status')
            if new_status:
                order.status = new_status # Assuming 'status' is a field in your Order model
                order.save()
                serializer = OrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"detail": "Status field is required in the request data."}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = Order.objects.get(id=pk)
            # Ensure the order belongs to the authenticated user
            if order.user != user.id:
                raise PermissionDenied("You do not have permission to cancel this order.")

            # Check if the order is already canceled or completed
            if order.status in ['canceled', 'completed']:
                return Response({"detail": f"Order is already {order.status}."}, status=status.HTTP_400_BAD_REQUEST)

            # Release reserved stock and return items to inventory
            for item in order.items:
                Product.objects(id=item.product.id).update_one(dec__reserved_inventory=item.quantity, inc__inventory=item.quantity)

            # Update order status
            order.status = 'canceled'
            order.save()
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
