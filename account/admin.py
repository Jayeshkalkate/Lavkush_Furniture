from django.contrib import admin
from django.contrib.auth.models import User
from .models import Items

# Optionally show Items inline with User in admin
class ItemsInline(admin.StackedInline):
    model = Items
    can_delete = False
    verbose_name_plural = 'Additional Info'

# Extend the default User admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    inlines = (ItemsInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')

# Unregister the original User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Also register Items separately, if needed
@admin.register(Items)
class ItemsAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'city')
    search_fields = ('user__username', 'phone_number', 'city')
