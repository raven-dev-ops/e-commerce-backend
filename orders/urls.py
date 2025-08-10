# orders/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, shipment_tracking_webhook

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("webhooks/shipment/", shipment_tracking_webhook, name="shipment-webhook"),
    path("", include(router.urls)),
]
