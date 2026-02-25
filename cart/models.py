from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from gallery.models import ImageWithCaption

# ===============================
# 🛒 CART MODEL
# ===============================


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"{self.user.username}'s Cart"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    @property
    def subtotal(self):
        return self.product.price * self.quantity  # Make sure product has price field

    def __str__(self):
        return f"{self.product.caption} x {self.quantity}"

