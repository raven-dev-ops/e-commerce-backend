from .models import Order, OrderItem, fields # Import fields if not already imported
import datetime
from django_mongoengine.mongo_admin.sites import site as mongo_admin_site

from django_mongoengine.mongo_admin.options import DocumentAdmin # Assuming you still need DocumentAdmin for OrderAdmin

class OrderAdmin(DocumentAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at', 'paid']
    inlines = [OrderItem] # Reference the OrderItem EmbeddedDocument
    def mark_as_shipped(self, request, queryset):
        # Assuming you have a 'shipped_date' field in your Order model
        count = queryset.update(shipped_date=datetime.date.today())
        self.message_user(request, f'{count} orders were successfully marked as shipped.')

    mark_as_shipped.short_description = "Mark selected orders as shipped"

    actions = ['mark_as_shipped']
