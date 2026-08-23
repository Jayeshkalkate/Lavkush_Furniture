from django.contrib import admin
from .models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'item__caption')
    raw_id_fields = ('user', 'item')