# reviews/admin.py

from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
from .models import Review


mongo_admin_site.register(Review)
