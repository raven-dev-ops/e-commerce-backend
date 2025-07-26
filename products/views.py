# products/views.py

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from products.models import Product
from products.serializers import ProductSerializer
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
    lookup_field = 'id'

    def get_object(self):
        pk = self.kwargs.get('pk')
        logging.info(f"Looking up Product with id: {pk}")
        try:
            # If _id is always a string in your DB, this is enough!
            return Product.objects.get(id=pk)
        except Product.DoesNotExist:
            logging.error(f"Product with id {pk} not found")
            raise Http404
        except Exception as e:
            logging.error(f"Error retrieving product: {e}")
            raise Http404

    def get_queryset(self):
        queryset = Product.objects.all()
        logging.info(f"Queryset object: Type={type(queryset)}, Representation={repr(queryset)}")
        logging.info(f"Raw PyMongo query: {queryset._query}")
        logging.info(f"Initial queryset length: {len(queryset)}")
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
