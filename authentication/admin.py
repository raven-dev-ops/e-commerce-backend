# authentication/admin.py

from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line1', 'city', 'state', 'postal_code')
    search_fields = ('user__username', 'address_line1', 'city')
