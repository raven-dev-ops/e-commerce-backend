"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Correct import
from django_mongoengine.mongo_admin import site as mongo_admin_site
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet
from orders.views import CartViewSet
from orders.views import OrderViewSet
from rest_framework.authtoken.views import obtain_auth_token
from . import views # Import the new view from the current app (backend)
from authentication.views import UserRegistrationView, UserProfileView, ProfileView
from authentication.views import AddressViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')

router.register(r'addresses', AddressViewSet, basename='address')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('mongo-admin/', mongo_admin_site.urls),
    path('api/', include(router.urls)),
    path('auth/', include('backend.authentication.urls')), # Include auth URLs under /auth/
    path('api/register/', UserRegistrationView.as_view(), name='user-registration'),
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('api/profile/', ProfileView.as_view(), name='user_profile'), # New profile URL pattern
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    path('webhook/', views.stripe_webhook_view, name='stripe_webhook'), # New webhook URL pattern
]
