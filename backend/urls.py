# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the e-commerce backend API!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('users/', include('users.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('cart/', include('cart.urls')),
    path('payments/', include('payments.urls')),
    path('discounts/', include('discounts.urls')),
    path('reviews/', include('reviews.urls')),
    path('authentication/', include('authentication.urls')),
    path('accounts/', include('allauth.urls')),
]