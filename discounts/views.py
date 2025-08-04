from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Discount
from products.models import Category
from .serializers import DiscountSerializer, CategorySerializer


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


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Category.objects.all()
