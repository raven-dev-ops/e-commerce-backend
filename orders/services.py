"""Service layer for order-related operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import logging

import stripe
from bson import ObjectId
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from authentication.models import Address
from cart.models import Cart, CartItem, get_or_create_user_ref
from orders.models import Order, OrderItem
from products.models import Product
from backend.currency import get_exchange_rate


logger = logging.getLogger(__name__)


@dataclass
class CartData:
    product: Product
    quantity: int


def _fetch_cart_items(cart: Cart) -> List[CartData]:
    """Return a list of cart items with resolved products."""

    cart_items = getattr(cart, "items", None)
    if cart_items is None:
        cart_id = getattr(cart, "id", None)
        if cart_id and ObjectId.is_valid(str(cart_id)):
            cart_items = list(CartItem.objects(cart=cart_id))
        else:
            cart_items = []
    else:
        cart_items = list(cart_items)

    items: List[CartData] = []
    for item in cart_items:
        product = Product.objects.get(id=item.product_id)
        items.append(CartData(product=product, quantity=item.quantity))
    return items


def create_order_from_cart(user, data) -> Order:
    """Create an order from the user's cart."""

    shipping_address_id = data.get("shipping_address_id")
    billing_address_id = data.get("billing_address_id")

    shipping_address: Optional[Address] = Address.objects.filter(
        user=user, is_default_shipping=True
    ).first()
    billing_address: Optional[Address] = Address.objects.filter(
        user=user, is_default_billing=True
    ).first()
    if shipping_address_id:
        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=user)
    if billing_address_id:
        billing_address = get_object_or_404(Address, id=billing_address_id, user=user)
    if not shipping_address:
        raise ValueError("Shipping address required.")
    if not billing_address:
        raise ValueError("Billing address required.")

    user_ref = get_or_create_user_ref(user)
    cart = Cart.objects(user=user_ref).first()
    if not cart:
        raise ValueError("Cart is empty.")

    try:
        items = _fetch_cart_items(cart)
    except Product.DoesNotExist as exc:
        raise ValueError(f"Product ID {exc.args[0]} not found.") from exc

    if not items:
        raise ValueError("Cart is empty.")

    subtotal = 0.0
    order_items: List[dict] = []
    product_updates: List[Tuple[Product, int]] = []

    for data_item in items:
        product = data_item.product
        quantity = data_item.quantity
        available = product.inventory - getattr(product, "reserved_inventory", 0)
        if quantity > available:
            raise ValueError(f"Insufficient stock for product {product.product_name}.")
        subtotal += product.price * quantity
        order_items.append(
            {
                "product_name": getattr(
                    product, "product_name", getattr(product, "name", "")
                ),
                "quantity": quantity,
                "unit_price": product.price,
            }
        )
        product_updates.append((product, quantity))

    shipping_cost = 5.0
    tax_amount = round(subtotal * 0.08, 2)
    total_price = subtotal + shipping_cost + tax_amount
    discount_code = discount_type = None
    discount_value = discount_amount = 0.0

    if getattr(cart, "discount", None):
        discount = cart.discount
        discount_code = discount.code
        discount_type = discount.discount_type
        discount_value = discount.value
        if discount.discount_type == "percentage":
            discount_amount = round(subtotal * discount.value / 100, 2)
        elif discount.discount_type == "fixed":
            discount_amount = min(discount.value, subtotal)
        subtotal -= discount_amount
        total_price = subtotal + shipping_cost + tax_amount

    currency = data.get("currency", "usd").lower()
    rate = 1.0
    if currency != "usd":
        try:
            rate = get_exchange_rate("usd", currency)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Currency conversion failed: %s", exc)
            raise ValueError("Currency conversion failed.") from exc

    if rate != 1.0:
        subtotal = round(subtotal * rate, 2)
        shipping_cost = round(shipping_cost * rate, 2)
        tax_amount = round(tax_amount * rate, 2)
        discount_amount = round(discount_amount * rate, 2)
        total_price = round(total_price * rate, 2)
        for item in order_items:
            item["unit_price"] = round(item["unit_price"] * rate, 2)

    stripe_secret_key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not stripe_secret_key:
        logger.error("STRIPE_SECRET_KEY is not configured")
        raise ValueError("Stripe configuration error.")

    stripe.api_key = stripe_secret_key
    payment_method_id = data.get("payment_method_id")
    if not payment_method_id:
        raise ValueError("Payment method required.")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(total_price * 100),
            currency=currency,
            payment_method=payment_method_id,
            confirmation_method="manual",
            confirm=True,
            metadata={"user_id": str(user.id)},
        )
    except stripe.error.CardError as exc:  # pragma: no cover - error path
        raise ValueError(f"Payment failed: {str(exc)}") from exc
    except Exception as exc:  # pragma: no cover - error path
        raise ValueError(f"Payment error: {str(exc)}") from exc

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            created_at=timezone.now(),
            shipping_address=shipping_address,
            billing_address=billing_address,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_price=total_price,
            currency=currency,
            payment_intent_id=intent.id,
            status="processing",
            discount_code=discount_code,
            discount_type=discount_type,
            discount_value=discount_value,
            discount_amount=discount_amount,
        )
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **item) for item in order_items]
        )

        for product, qty in product_updates:
            Product.objects.filter(id=product.id).update(
                reserved_inventory=F("reserved_inventory") + qty
            )

        if getattr(cart, "discount", None) and hasattr(cart.discount, "times_used"):
            cart.discount.times_used += 1
            cart.discount.save()

    cart.items = []
    cart.discount = None
    cart.save()
    cart_id = getattr(cart, "id", None)
    if cart_id and ObjectId.is_valid(str(cart_id)):
        try:
            CartItem.objects(cart=cart_id).delete()
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to delete cart items")

    return order


def release_reserved_inventory(order: Order) -> None:
    """Return reserved stock to inventory when an order is not completed."""

    for item in order.items.all():
        product = Product.objects.filter(product_name=item.product_name).first()
        if not product:
            logger.warning(
                "Product %s not found when releasing inventory", item.product_name
            )
            continue
        current_reserved = getattr(product, "reserved_inventory", 0)
        new_reserved = max(current_reserved - item.quantity, 0)
        Product.objects(pk=product.id).update(set__reserved_inventory=new_reserved)
