from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.core.cache import cache

from .models import Discount
from products.models import Category
from backend.serializers.discounts import DiscountSerializer, CategorySerializer


CATEGORY_LIST_CACHE_KEY = "category_list"


class DiscountListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Discount.objects.all()


class DiscountRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Discount.objects.all()


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Category.objects.all()

    def list(self, request, *args, **kwargs):
        cached = cache.get(CATEGORY_LIST_CACHE_KEY)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(CATEGORY_LIST_CACHE_KEY, response.data, 300)
        return response

    def perform_create(self, serializer):
        category = serializer.save()
        cache.delete(CATEGORY_LIST_CACHE_KEY)
        return category


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Category.objects.all()

    def perform_update(self, serializer):
        category = serializer.save()
        cache.delete(CATEGORY_LIST_CACHE_KEY)
        return category

    def perform_destroy(self, instance):
        instance.delete()
        cache.delete(CATEGORY_LIST_CACHE_KEY)
