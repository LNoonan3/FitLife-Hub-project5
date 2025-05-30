from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'fitness_goal', 'created_at')
    search_fields = ('user__username', 'fitness_goal')
