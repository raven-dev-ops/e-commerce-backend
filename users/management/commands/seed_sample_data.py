import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from products.models import Category, Product


class Command(BaseCommand):
    """Seed the database with demo data for development."""

    help = "Create a demo user along with sample categories and products."

    def handle(self, *args, **options):
        User = get_user_model()

        if not User.objects.filter(username="demo").exists():
            password = os.environ.get("DEMO_USER_PASSWORD") or get_random_string()
            User.objects.create_user(
                username="demo",
                email="demo@example.com",
                password=password,
            )
            message = "Created demo user."
            if "DEMO_USER_PASSWORD" not in os.environ:
                message += f" Generated password: {password}"
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stdout.write("Demo user already exists.")

        if not Category.objects(name="Skincare").first():
            category = Category(name="Skincare", description="Skincare products")
            category.save()

            Product(
                product_name="Sample Lotion",
                category=category.name,
                description="A soothing lotion for demonstration purposes.",
                price=19.99,
                inventory=100,
            ).save()

            Product(
                product_name="Sample Cleanser",
                category=category.name,
                description="A gentle cleanser for demonstration purposes.",
                price=9.99,
                inventory=150,
            ).save()

            self.stdout.write(self.style.SUCCESS("Created sample products."))
        else:
            self.stdout.write("Sample products already exist.")
