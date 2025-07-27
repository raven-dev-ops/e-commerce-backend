# payments/admin.py

from django.contrib import admin
from .models import Payment, Transaction

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'invoice', 'amount', 'method', 'payment_date')
    list_filter = ('method', 'payment_date')
    search_fields = ('user__username', 'user__email', 'invoice')
    ordering = ('-payment_date',)
    autocomplete_fields = ('user',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'status', 'processed_at')
    list_filter = ('status', 'processed_at')
    search_fields = ('payment__invoice', 'payment__user__username', 'status')
    ordering = ('-processed_at',)
    autocomplete_fields = ('payment',)
