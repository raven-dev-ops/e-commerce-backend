from __future__ import annotations

"""Utilities for currency conversion."""

from typing import Any

import requests  # type: ignore[import]
from django.conf import settings


DEFAULT_API = "https://api.exchangerate.host/latest"


def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Fetch exchange rate from `from_currency` to `to_currency` using an external API."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency == to_currency:
        return 1.0
    url = getattr(settings, "EXCHANGE_RATE_API_URL", DEFAULT_API)
    response = requests.get(
        url, params={"base": from_currency, "symbols": to_currency}, timeout=5
    )
    response.raise_for_status()
    data: Any = response.json()
    rates = data.get("rates", {})
    rate = rates.get(to_currency)
    if rate is None:
        raise ValueError("Exchange rate not available")
    return float(rate)


def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert an amount between currencies using real-time rates."""
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)
