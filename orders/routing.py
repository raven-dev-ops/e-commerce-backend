from django.urls import path

from .consumers import OrderStatusConsumer

websocket_urlpatterns = [
    path("ws/orders/<int:order_id>/", OrderStatusConsumer.as_asgi()),
]
