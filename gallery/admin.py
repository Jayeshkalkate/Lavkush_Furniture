from django.contrib import admin
from django.db.models import Avg
from django.db import models
from .models import Category, ImageWithCaption, ProductImage, Rating

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'product_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=models.Count('products'))

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(ImageWithCaption)
class ImageWithCaptionAdmin(admin.ModelAdmin):
    list_display = ('caption', 'sku', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured', 'get_avg_rating')
    list_editable = ('price', 'stock_quantity', 'is_active', 'is_featured')
    search_fields = ('caption', 'sku', 'description', 'materials', 'color')
    list_filter = ('category', 'is_active', 'is_featured', 'materials', 'uploaded_at')
    prepopulated_fields = {'slug': ('caption',)}
    readonly_fields = ('uploaded_at', 'updated_at', 'sku')
    inlines = [ProductImageInline]
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    def get_avg_rating(self, obj):
        return round(obj.get_avg_rating(), 1) if obj.get_avg_rating() else '—'
    get_avg_rating.short_description = 'Rating'

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'rating', 'approved', 'created_at')
    list_filter = ('rating', 'approved', 'created_at')
    search_fields = ('user__username', 'item__caption', 'title', 'review_text')
    raw_id_fields = ('user', 'item')
