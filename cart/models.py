"""
Legacy cart models have been removed now that cart
state and products are handled entirely on the frontend.

This module is kept only so imports like `from cart.models import Cart`
do not break, but no database models are defined anymore.
"""

__all__: list[str] = []
