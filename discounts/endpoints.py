from django.urls import path
from .views import (
    DiscountListCreateAPIView,
    DiscountRetrieveUpdateDestroyAPIView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path(
        "discounts/", DiscountListCreateAPIView.as_view(), name="discount-list-create"
    ),
    path(
        "discounts/<str:pk>/",
        DiscountRetrieveUpdateDestroyAPIView.as_view(),
        name="discount-detail",
    ),
    path(
        "categories/", CategoryListCreateAPIView.as_view(), name="category-list-create"
    ),
    path(
        "categories/<str:pk>/",
        CategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="category-detail",
    ),
]
