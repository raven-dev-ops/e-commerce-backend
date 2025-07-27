# orders/admin.py

from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'status', 'total_price')
    search_fields = ('user__username', 'status', 'payment_intent_id')
    list_filter = ('status',)
