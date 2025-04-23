from django.contrib import admin
from .models import ImageWithCaption, Rating
from django.db.models import Avg

class ImageWithCaptionAdmin(admin.ModelAdmin):
    # Include new fields in the list display and enable editing
    list_display = ('caption', 'price', 'uploaded_at', 'description', 'dimensions', 'materials', 'get_avg_rating')
    list_editable = ('price', 'description', 'dimensions', 'materials')  # Enable editing of these fields in the list view
    search_fields = ('caption', 'description', 'materials')  # Add search capabilities for the new fields

    # Custom method to calculate the average rating for each image
    def get_avg_rating(self, obj):
        avg_rating = Rating.objects.filter(item=obj).aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 2) if avg_rating else 'No Ratings'
    get_avg_rating.short_description = 'Avg. Rating'  # Column header for the custom method

# Register the model with the updated admin class
admin.site.register(ImageWithCaption, ImageWithCaptionAdmin)
