# products/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from products.models import Product
from products.filters import ProductFilter
from products.serializers import ProductSerializer
from bson.objectid import ObjectId
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django.http import Http404
import logging

class CustomProductPagination(PageNumberPagination):
    page_size = 100

class ProductViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['product_name', 'description', 'tags', 'category']
    pagination_class = CustomProductPagination
    lookup_field = '_id' 

    def get_object(self):
        lookup_value = self.kwargs.get(self.lookup_field)
        try:
            # Try as ObjectId first, fallback to plain string
            try:
                obj = Product.objects.get(id=ObjectId(lookup_value))
            except Exception:
                obj = Product.objects.get(id=lookup_value)
            return obj
        except Product.DoesNotExist:
            raise Http404
        except Exception as e:
            logging.error(f"Error retrieving product: {e}")
            raise Http404

    def get_queryset(self):
        queryset = Product.objects.all()
        logging.info(f"Queryset object: Type={type(queryset)}, Representation={repr(queryset)}")
        logging.info(f"Raw PyMongo query: {getattr(queryset, '_query', None)}")
        filter_params = self.request.query_params
        logging.info(f"Initial queryset length: {len(queryset)}")
        # Manual filtering can be implemented here if needed
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
