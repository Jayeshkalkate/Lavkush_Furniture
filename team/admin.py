from django.contrib import admin
from .models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'is_visible')
    list_filter = ('is_visible',)
    search_fields = ('name', 'role', 'bio')
    readonly_fields = ('image',)