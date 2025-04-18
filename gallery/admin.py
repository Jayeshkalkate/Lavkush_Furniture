from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ImageWithCaption

class ImageWithCaptionAdmin(admin.ModelAdmin):
    list_display = ('caption', 'price', 'uploaded_at')
    list_editable = ('price',)
    search_fields = ('caption',)

admin.site.register(ImageWithCaption, ImageWithCaptionAdmin)
