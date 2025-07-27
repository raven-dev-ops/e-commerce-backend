# payments/admin.py

from django.contrib import admin
from .models import Payment, Transaction

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'amount', 'method', 'payment_date')
    list_filter = ('method', 'payment_date')
    search_fields = ('invoice__invoice_number',)
    ordering = ('-payment_date',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'status', 'processed_at')
    list_filter = ('status', 'processed_at')
    search_fields = ('payment__id',)
    ordering = ('-processed_at',)
