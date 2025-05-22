from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
from .models import Product
from django_mongoengine.mongo_admin.options import DocumentAdmin

mongo_admin_site.register(Product)
