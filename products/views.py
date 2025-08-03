# products/views.py

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from products.models import Product
from products.serializers import ProductSerializer
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
from django.core.cache import cache
import logging


class CustomProductPagination(PageNumberPagination):
    page_size = 100


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
    lookup_field = "_id"  # Use '_id' for MongoDB string primary key

    def get_object(self):
        pk = self.kwargs.get(self.lookup_field)
        logging.info(
            f"[ProductViewSet] Attempting to serve detail for Product _id: {pk}"
        )
        cache_key = f"product:{pk}"
        product = cache.get(cache_key)
        if product:
            return product
        try:
            product = Product.objects.get(_id=str(pk))
            cache.set(cache_key, product, 300)
            return product
        except Product.DoesNotExist:
            logging.error(f"[ProductViewSet] Product with _id {pk} not found")
            raise Http404
        except Exception as e:
            logging.error(f"[ProductViewSet] Error retrieving product: {e}")
            raise Http404

    def get_queryset(self):
        queryset = Product.objects.all()
        logging.info(f"[ProductViewSet] Serving {queryset.count()} products.")
        return queryset

    def list(self, request, *args, **kwargs):
        cache_key = "product_list"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 300)
        return response

    def perform_create(self, serializer):
        product = serializer.save()
        cache.set(f"product:{product._id}", product, 300)
        cache.delete("product_list")

    def perform_update(self, serializer):
        product = serializer.save()
        cache.set(f"product:{product._id}", product, 300)
        cache.delete("product_list")

    def perform_destroy(self, instance):
        cache.delete(f"product:{instance._id}")
        cache.delete("product_list")
        instance.delete()
