from django.contrib import admin
from .models import Cart, CartItem
from .models import Payment, Order

admin.site.register(Cart)
admin.site.register(CartItem)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "is_settled", "created_at")
    list_filter = ("status", "is_settled")
    search_fields = ("user__username", "payment_id", "order_id")
    actions = ["mark_as_settled"]

    def mark_as_settled(self, request, queryset):
        queryset.update(is_settled=True)

    mark_as_settled.short_description = "Mark selected payments as Settled"


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
