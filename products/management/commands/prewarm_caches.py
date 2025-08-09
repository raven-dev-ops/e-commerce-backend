from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory
from products.views import ProductViewSet
from products.models import Product
from discounts.views import CategoryListCreateAPIView


class Command(BaseCommand):
    help = "Pre-warm caches for frequently accessed endpoints."

    def handle(self, *args, **options):
        factory = APIRequestFactory()

        # Warm product list cache
        request = factory.get("/products/")
        list_view = ProductViewSet.as_view({"get": "list"})
        response = list_view(request)
        response.render()
        self.stdout.write(self.style.SUCCESS("Warmed product list cache"))

        # Warm individual product caches
        detail_view = ProductViewSet.as_view({"get": "retrieve"})
        for product in Product.objects.all():
            request = factory.get(f"/products/{product.slug}/")
            response = detail_view(request, slug=product.slug)
            response.render()
        self.stdout.write(self.style.SUCCESS("Warmed product detail caches"))

        # Warm category list cache
        request = factory.get("/categories/")
        category_view = CategoryListCreateAPIView.as_view()
        response = category_view(request)
        response.render()
        self.stdout.write(self.style.SUCCESS("Warmed category list cache"))
