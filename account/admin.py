from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Items


@admin.register(Items)
class ItemsAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'city')
    search_fields = ('user__username', 'phone_number', 'city')
    raw_id_fields = ('user',)  # useful for large user tables


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')
    # Optionally add an inline for Items if desired, but left out as requested


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)