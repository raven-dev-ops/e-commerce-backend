from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
from .models import Discount, Category

mongo_admin_site.register(Discount)
mongo_admin_site.register(Category)