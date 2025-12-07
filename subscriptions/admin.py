from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'interval', 'is_active', 'active_subs_count')
    search_fields = ('name', 'description')
    list_filter = ('interval', 'is_active')
    list_editable = ('is_active',)
    ordering = ('price',)
    
    def price_display(self, obj):
        return f"€{obj.price:.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def active_subs_count(self, obj):
        active_count = obj.subscription_set.filter(status='active').count()
        if active_count > 0:
            return format_html(
                '<span style="color: green;">✓ {} active</span>',
                active_count
            )
        return format_html('<span style="color: gray;">No active subs</span>')
    active_subs_count.short_description = 'Active Subscriptions'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'is_expired')
    list_filter = ('status', 'plan', 'start_date')
    search_fields = ('user__username', 'user__email', 'stripe_sub_id')
    readonly_fields = ('start_date', 'stripe_sub_id')
    list_editable = ('status',)
    ordering = ('-start_date',)
    
    def is_expired(self, obj):
        from django.utils import timezone
        if obj.end_date and obj.end_date < timezone.now().date():
            return format_html('<span style="color: red; font-weight: bold;">✗ Expired</span>')
        return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
    is_expired.short_description = 'Expiry Status'
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'next_payment_date')
        }),
        ('Payment Information', {
            'fields': ('stripe_sub_id',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['cancel_subscriptions']
    
    def cancel_subscriptions(self, request, queryset):
        count = queryset.update(status='canceled')
        self.message_user(request, f"{count} subscription(s) cancelled.")
    cancel_subscriptions.short_description = "Cancel selected subscriptions"