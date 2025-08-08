from __future__ import annotations

"""Elasticsearch-backed product search utilities."""

from typing import Any, List
from elasticsearch import Elasticsearch
from django.conf import settings

# Create a client instance using configured URL
_es_client = Elasticsearch(settings.ELASTICSEARCH_URL)


def search_products(query: str) -> List[dict[str, Any]]:
    """Search products using Elasticsearch.

    Parameters
    ----------
    query: str
        The user-provided search string.

    Returns
    -------
    list of dict
        A list of product documents returned by Elasticsearch.
    """
    response = _es_client.search(
        index="products",
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["product_name", "description", "tags", "category"],
                }
            }
        },
    )
    hits = response.get("hits", {}).get("hits", [])
    return [hit.get("_source", {}) for hit in hits]
