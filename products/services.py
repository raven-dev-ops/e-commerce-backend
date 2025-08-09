"""Service layer for product-related operations."""

from __future__ import annotations

from typing import List

from orders.models import OrderItem
from products.models import Product


def get_recommended_products(user, limit: int = 5) -> List[Product]:
    """Return products recommended for ``user`` based on purchase history.

    Recommendations are derived from the categories of previously purchased
    products. Products the user has already purchased are excluded, and results
    are ordered by average rating in descending order.
    """

    purchased_names = list(
        OrderItem.objects.filter(order__user=user).values_list(
            "product_name", flat=True
        )
    )
    if not purchased_names:
        return []

    purchased_products = Product.objects(product_name__in=purchased_names)
    categories = {p.category for p in purchased_products}
    if not categories:
        return []

    recommended_qs = Product.objects(
        category__in=list(categories), product_name__nin=purchased_names
    ).order_by("-average_rating")
    return list(recommended_qs[:limit])
