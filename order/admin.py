from django.contrib import admin
from .models import Coupon, Payment, Order, OrderItem
from .email_utils import send_order_event_email

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal', 'product_name', 'sku', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'total_amount', 'order_status', 'tracking_number', 'created_at')
    list_filter = ('order_status', 'return_status', 'created_at')
    search_fields = ('invoice_number', 'user__username', 'email', 'phone', 'tracking_number', 'shipping_address')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'subtotal', 'shipping_amount', 'tax_amount', 'discount_amount')
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            old_status = Order.objects.filter(pk=obj.pk).values_list('order_status', flat=True).first()
        from django.utils import timezone
        if obj.order_status == 'shipped' and not obj.shipped_at:
            obj.shipped_at = timezone.now()
        if obj.order_status == 'delivered' and not obj.delivered_at:
            obj.delivered_at = timezone.now()
            if not obj.shipped_at:
                obj.shipped_at = obj.delivered_at
        super().save_model(request, obj, form, change)
        if change and old_status != obj.order_status and obj.order_status in {'shipped', 'delivered', 'cancelled', 'return_pending', 'returned'}:
            from django.db import transaction
            transaction.on_commit(lambda: send_order_event_email(obj, obj.order_status))
    fieldsets = (
        ('Order', {'fields': ('invoice_number', 'user', 'payment', 'order_status', 'created_at', 'updated_at')}),
        ('Amounts', {'fields': ('subtotal', 'shipping_amount', 'tax_amount', 'discount_amount', 'total_amount')}),
        ('Delivery snapshot', {'fields': ('first_name', 'last_name', 'company', 'shipping_address', 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone', 'email', 'order_notes')}),
        ('Shipping', {'fields': ('shipping_method', 'shipping_provider', 'tracking_number', 'expected_delivery', 'shipped_at', 'delivered_at')}),
        ('Cancellation & returns', {'fields': ('cancellation_reason', 'return_requested', 'return_reason', 'return_status')}),
        ('Inventory', {'fields': ('inventory_deducted',)}),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'gateway_status', 'is_settled', 'created_at', 'paid_at')
    list_filter = ('status', 'is_settled', 'gateway_status', 'created_at')
    search_fields = ('user__username', 'payment_id', 'order_id', 'order__invoice_number')
    readonly_fields = ('order_id', 'payment_id', 'signature', 'gateway_response', 'created_at', 'paid_at', 'refunded_at')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'active', 'uses', 'usage_limit', 'valid_until')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)
    list_editable = ('active',)
