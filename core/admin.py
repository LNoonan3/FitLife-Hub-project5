from django.contrib import admin
from django.utils.html import format_html
from .models import ProgressUpdate, NewsletterSubscriber


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Update Information', {
            'fields': ('user', 'title', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    search_fields = ('email',)
    list_filter = ('subscribed_at',)
    readonly_fields = ('subscribed_at',)
    ordering = ('-subscribed_at',)
    actions = ['mark_as_active', 'mark_as_inactive']

    def is_active(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">✓ Active</span>'
        )
    is_active.short_description = 'Status'

    def mark_as_active(self, request, queryset):
        self.message_user(
            request,
            f"{queryset.count()} subscribers marked as active."
        )
    mark_as_active.short_description = "Mark selected as active"

    def mark_as_inactive(self, request, queryset):
        self.message_user(
            request,
            f"{queryset.count()} subscribers marked as inactive."
        )
    mark_as_inactive.short_description = "Mark selected as inactive"
