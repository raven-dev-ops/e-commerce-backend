# products/views.py

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import action
from django.http import Http404, HttpResponse
from django.core.cache import cache
from products.filters import ProductFilter
from products.models import Product
from products.serializers import ProductSerializer
import csv
from io import TextIOWrapper
import logging
from products.search import search_products


class CustomProductPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ["product_name", "description", "tags", "category"]
    pagination_class = CustomProductPagination
    lookup_field = "slug"
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "bulk_import",
            "bulk_export",
        ]:
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        logging.info(
            f"[ProductViewSet] Attempting to serve detail for Product slug: {pk}"
        )
        cache_key = f"product:{pk}"
        product = cache.get(cache_key)
        if product:
            return product
        try:
            product = Product.objects.get(slug=str(pk))
            cache.set(cache_key, product, 300)
            return product
        except Product.DoesNotExist:
            logging.error(f"[ProductViewSet] Product with slug {pk} not found")
            raise Http404
        except Exception as e:
            logging.error(f"[ProductViewSet] Error retrieving product: {e}")
            raise Http404

    def get_queryset(self):
        queryset = Product.objects.all()
        filterset = ProductFilter(self.request.query_params, queryset=queryset)
        queryset = filterset.qs
        logging.info(f"[ProductViewSet] Serving {queryset.count()} products.")
        return queryset

    def list(self, request, *args, **kwargs):
        params = request.query_params
        if params:
            serialized = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key = f"product_list:{serialized}"
        else:
            cache_key = "product_list"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        """Search products using Elasticsearch."""
        query = request.query_params.get("q")
        if not query:
            return Response({"detail": "Missing query"}, status=400)
        results = search_products(query)
        return Response(results)

    def perform_create(self, serializer):
        product = serializer.save()
        cache.set(f"product:{product.slug}", product, 300)
        cache.delete("product_list")

    def perform_update(self, serializer):
        product = serializer.save()
        cache.set(f"product:{product.slug}", product, 300)
        cache.delete("product_list")

    def perform_destroy(self, instance):
        cache.delete(f"product:{instance.slug}")
        cache.delete("product_list")
        instance.delete()

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request, *args, **kwargs):
        """Import products from an uploaded CSV file."""
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file provided"}, status=400)
        created = 0
        reader = csv.DictReader(TextIOWrapper(file_obj.file, encoding="utf-8"))
        for row in reader:
            data = {
                "product_name": row.get("product_name", ""),
                "category": row.get("category", ""),
                "description": row.get("description", ""),
                "price": row.get("price", "0"),
                "ingredients": [
                    i.strip()
                    for i in row.get("ingredients", "").split("|")
                    if i.strip()
                ],
                "benefits": [
                    i.strip() for i in row.get("benefits", "").split("|") if i.strip()
                ],
                "tags": [
                    i.strip() for i in row.get("tags", "").split("|") if i.strip()
                ],
                "inventory": int(row.get("inventory", 0) or 0),
                "reserved_inventory": 0,
            }
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created += 1
        return Response({"imported": created}, status=201)

    @action(detail=False, methods=["get"], url_path="bulk-export")
    def bulk_export(self, request, *args, **kwargs):
        """Export products as a CSV file."""
        fieldnames = [
            "product_name",
            "category",
            "description",
            "price",
            "inventory",
            "ingredients",
            "benefits",
            "tags",
        ]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=products.csv"
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for product in Product.objects.all():
            writer.writerow(
                {
                    "product_name": product.product_name,
                    "category": product.category,
                    "description": product.description,
                    "price": product.price,
                    "inventory": product.inventory,
                    "ingredients": "|".join(product.ingredients),
                    "benefits": "|".join(product.benefits),
                    "tags": "|".join(product.tags),
                }
            )
        return response
