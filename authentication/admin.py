from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
from .models import Address

mongo_admin_site.register(Address)
