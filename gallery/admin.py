from django.contrib import admin
from django.db.models import Avg
from .models import ImageWithCaption, Rating


class ImageWithCaptionAdmin(admin.ModelAdmin):
    list_display = ('caption', 'price', 'uploaded_at', 'materials', 'get_avg_rating')
    list_editable = ('price',)  # only price editable in list view to avoid issues
    search_fields = ('caption', 'description', 'materials')
    list_filter = ('uploaded_at', 'materials')
    readonly_fields = ('uploaded_at',)

    def get_avg_rating(self, obj):
        avg = obj.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 'No Ratings'
    get_avg_rating.short_description = 'Avg Rating'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'item__caption')
    raw_id_fields = ('user', 'item')


admin.site.register(ImageWithCaption, ImageWithCaptionAdmin)