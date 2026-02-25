from django.contrib import admin
from .models import Payment, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "user",
        "total_amount",
        "order_status",
        "created_at",
    )
    list_filter = ("order_status",)
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "is_settled", "created_at")
    list_filter = ("status", "is_settled")
    search_fields = ("user__username", "payment_id", "order_id")
