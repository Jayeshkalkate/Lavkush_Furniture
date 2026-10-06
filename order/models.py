import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Payment(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', db_index=True)
    order_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    is_settled = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gateway_status = models.CharField(max_length=50, blank=True)
    webhook_event = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.payment_id or self.order_id or self.pk}'


class Coupon(models.Model):
    DISCOUNT_TYPES = (('percent', 'Percentage'), ('fixed', 'Fixed amount'))
    code = models.CharField(max_length=40, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percent')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    uses = models.PositiveIntegerField(default=0)
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code

    def is_valid(self, subtotal):
        now = timezone.now()
        if not self.active or subtotal < self.minimum_order_value:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit is not None and self.uses >= self.usage_limit:
            return False
        return self.value > 0

    def discount_for(self, subtotal):
        if not self.is_valid(subtotal):
            return Decimal('0.00')
        if self.discount_type == 'percent':
            amount = subtotal * self.value / Decimal('100')
        else:
            amount = self.value
        return min(max(amount, Decimal('0.00')), subtotal).quantize(Decimal('0.01'))


class Order(models.Model):
    ORDER_STATUS = (
        ('payment_pending', 'Payment Pending'),
        ('processing', 'Processing'), ('shipped', 'Shipped'),
        ('delivered', 'Delivered'), ('cancelled', 'Cancelled'),
        ('return_pending', 'Return Requested'), ('returned', 'Returned'),
    )
    RETURN_STATUS = (('none', 'None'), ('requested', 'Requested'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', db_index=True)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, related_name='order', null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=40, blank=True)
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS, default='payment_pending', db_index=True)
    invoice_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=160, blank=True)
    shipping_address = models.TextField()
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=80, default='India')
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    order_notes = models.TextField(blank=True)
    shipping_method = models.CharField(max_length=100, default='Standard delivery')
    tracking_number = models.CharField(max_length=120, blank=True)
    shipping_provider = models.CharField(max_length=120, blank=True)
    expected_delivery = models.DateField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    return_requested = models.BooleanField(default=False)
    return_reason = models.TextField(blank=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS, default='none')
    inventory_deducted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at']), models.Index(fields=['order_status', '-created_at'])]

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f'LF-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.invoice_number}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', db_index=True)
    product = models.ForeignKey('gallery.ImageWithCaption', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=80, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
