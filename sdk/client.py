from __future__ import annotations

from typing import Any, Dict, Optional

import requests  # type: ignore[import-untyped]


class ECommerceClient:
    """Lightweight client for interacting with the e-commerce API."""

    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_products(self, params: Optional[Dict[str, Any]] = None) -> Any:
        """Return a list of products from the API."""
        url = f"{self.base_url}/api/v1/products/"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
