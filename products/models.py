"""
Legacy product models have been removed. The product catalog now lives
in the frontend static files.

This module is kept only so imports like `from products.models import Product`
do not break at import time, but no ORM models are defined.
"""

__all__: list[str] = []
