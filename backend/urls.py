# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse

def home(request):
    return HttpResponse("Welcome to the e-commerce backend API!")

def custom_404(request, exception=None):
    return JsonResponse({'error': 'Endpoint not found'}, status=404)

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
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/social/', include('allauth.socialaccount.urls')),
]

handler404 = 'backend.urls.custom_404'
