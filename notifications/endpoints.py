from django.urls import path

from .views import notifications_stream

urlpatterns = [
    path("stream/", notifications_stream, name="notifications-stream"),
]
