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

class CustomProductPagination(PageNumberPagination):
    page_size = 10

class ProductViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter]
    search_fields = ['product_name', 'description', 'tags', 'category']
    pagination_class = CustomProductPagination

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            return Product.objects.get(id=ObjectId(pk))
        except Product.DoesNotExist:
 Http404
        except Exception as e:
            # Optional: log or handle invalid ObjectId errors
            raise Http404

    def get_queryset(self):
        queryset = Product.objects.all()
        filter_params = self.request.query_params

        # Implement manual filtering based on ProductFilter fields
        for field_name, lookup_expr in ProductFilter.Meta.fields.items():
            if field_name in filter_params:
                filter_kwargs = {f'{field_name}__{lookup_expr}': filter_params[field_name]}
                queryset = queryset.filter(**filter_kwargs)
 return queryset # Added return statement

 def perform_create(self, serializer):
 serializer.save()

    def perform_update(self, serializer):
 serializer.save()
