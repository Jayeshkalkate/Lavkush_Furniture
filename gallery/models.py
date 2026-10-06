from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class ImageWithCaption(models.Model):
    image = CloudinaryField('image', blank=True, null=True)
    caption = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True, null=True, db_index=True)
    sku = models.CharField(max_length=80, unique=True, blank=True, null=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    description = models.TextField(blank=True)
    dimensions = models.CharField(max_length=120, blank=True)
    materials = models.CharField(max_length=255, blank=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    color = models.CharField(max_length=100, blank=True)
    stock_quantity = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    warranty = models.CharField(max_length=120, blank=True)
    lead_time = models.CharField(max_length=120, blank=True)
    care_instructions = models.TextField(blank=True)
    meta_title = models.CharField(max_length=180, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ['-is_featured', '-uploaded_at']
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0), name='product_price_non_negative')]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.caption)[:260] or 'furniture'
            candidate = base
            counter = 2
            while type(self).objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base}-{counter}'
                counter += 1
            self.slug = candidate
        if not self.sku:
            self.sku = f'LF-{(self.pk or 0):05d}' if self.pk else None
        super().save(*args, **kwargs)
        if not self.sku:
            self.sku = f'LF-{self.pk:05d}'
            super().save(update_fields=['sku'])

    def __str__(self):
        return self.caption

    def get_avg_rating(self):
        return self.ratings.filter(approved=True).aggregate(avg=models.Avg('rating'))['avg'] or 0

    @property
    def review_count(self):
        return self.ratings.filter(approved=True, review_text__gt='').count()

    @property
    def in_stock(self):
        return self.is_active and self.stock_quantity > 0

    def get_absolute_url(self):
        return reverse('furniture_detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE, related_name='gallery_images')
    image = CloudinaryField('image', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.product.caption} image {self.pk}'


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    item = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE, related_name='ratings', db_index=True)
    rating = models.PositiveIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=160, blank=True)
    review_text = models.TextField(blank=True)
    approved = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'item'], name='unique_user_product_rating')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} rated {self.item.caption} {self.rating} stars'
