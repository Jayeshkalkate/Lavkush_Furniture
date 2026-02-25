# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


# ===============================
# 💳 PAYMENT MODEL
# ===============================


class Payment(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")

    order_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # Razorpay order ID
    payment_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # Razorpay payment ID
    signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    is_settled = models.BooleanField(default=False)  # Bank settlement status
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.payment_id or 'No Payment ID'}"



# ===============================
# 📦 ORDER MODEL
# ===============================


class Order(models.Model):

    ORDER_STATUS = (
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    payment = models.OneToOneField(
        Payment, on_delete=models.CASCADE, related_name="order", null=True, blank=True
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    order_status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default="processing"
    )

    invoice_number = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# ===============================
# 🧾 ORDER ITEMS
# ===============================


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
