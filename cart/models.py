from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from gallery.models import ImageWithCaption


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_total(self):
        """Calculate total price with caching to avoid repeated DB hits."""
        if hasattr(self, '_total_cache'):
            return self._total_cache
        total = sum(item.subtotal for item in self.items.all())
        self._total_cache = total
        return total

    @property
    def total_amount(self):
        return self.get_total()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ('cart', 'product')  # Prevent duplicate items

    @property
    def subtotal(self):
        # Ensure product has a 'price' field (float or Decimal)
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product.caption} x {self.quantity}"