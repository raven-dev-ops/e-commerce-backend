from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# Temporarily comment these to avoid MongoDB connection errors during migration
# from .models import Discount, Category
from .serializers import DiscountSerializer, CategorySerializer

# Dummy stubs for migration
class Discount:
    objects = []

class Category:
    objects = []

class DiscountListCreateAPIView(generics.ListCreateAPIView):
    queryset = Discount.objects  # empty list
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class DiscountRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Discount.objects
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
