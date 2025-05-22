# users/admin.py
from .models import User
from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
mongo_admin_site.register(User)
