# authentication/admin.py

from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street', 'city', 'state', 'country', 'zip_code', 'is_default_shipping', 'is_default_billing', 'created_at')
    search_fields = ('user__username', 'user__email', 'street', 'city', 'state', 'country', 'zip_code')
    list_filter = ('is_default_shipping', 'is_default_billing', 'country', 'state')
    ordering = ('-created_at',)
    autocomplete_fields = ('user',)
