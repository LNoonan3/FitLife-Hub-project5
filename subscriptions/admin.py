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
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'is_expired', 'stripe_sub_id')
    list_filter = ('status', 'plan', 'start_date')
    search_fields = ('user__username', 'user__email', 'stripe_sub_id')
    readonly_fields = ('start_date', 'created_at', 'updated_at')
    list_editable = ('status',)
    ordering = ('-start_date',)

    def is_expired(self, obj):
        from django.utils import timezone
        if obj.status == 'canceled':
            return format_html('<span style="color: orange;">✗ Canceled</span>')
        elif obj.end_date and obj.end_date < timezone.now().date():
            return format_html('<span style="color: red; font-weight: bold;">✗ Expired</span>')
        elif obj.status == 'active':
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: gray;">-</span>')
    is_expired.short_description = 'Status Check'

    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan', 'status', 'stripe_sub_id')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'next_payment_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['cancel_subscriptions', 'sync_with_stripe', 'fix_duplicate_active']

    def cancel_subscriptions(self, request, queryset):
        import stripe
        from django.conf import settings
        from django.utils import timezone

        stripe.api_key = settings.STRIPE_SECRET_KEY
        count = 0

        for sub in queryset.filter(status='active'):
            try:
                # Cancel on Stripe
                stripe.Subscription.delete(sub.stripe_sub_id)
            except stripe.error.InvalidRequestError:
                pass  # Already canceled on Stripe
            except Exception as e:
                self.message_user(request, f"Error canceling {sub.id}: {str(e)}", level='ERROR')
                continue

            # Update local database
            sub.status = 'canceled'
            sub.end_date = timezone.now().date()
            sub.save()
            count += 1

        self.message_user(request, f"{count} subscription(s) canceled successfully.")
    cancel_subscriptions.short_description = "Cancel selected subscriptions"

    def sync_with_stripe(self, request, queryset):
        import stripe
        from django.conf import settings
        from django.utils import timezone

        stripe.api_key = settings.STRIPE_SECRET_KEY
        synced = 0
        errors = 0

        for sub in queryset:
            try:
                # Fetch from Stripe
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_sub_id)

                # Update local status based on Stripe
                if stripe_sub.status == 'active':
                    sub.status = 'active'
                    sub.end_date = None
                elif stripe_sub.status in ['canceled', 'incomplete_expired']:
                    sub.status = 'canceled'
                    if not sub.end_date:
                        sub.end_date = timezone.now().date()
                elif stripe_sub.status == 'past_due':
                    sub.status = 'past_due'

                sub.save()
                synced += 1
            except stripe.error.InvalidRequestError:
                # Subscription doesn't exist on Stripe
                sub.status = 'canceled'
                if not sub.end_date:
                    sub.end_date = timezone.now().date()
                sub.save()
                synced += 1
            except Exception as e:
                errors += 1
                self.message_user(request, f"Error syncing {sub.id}: {str(e)}", level='ERROR')

        self.message_user(request, f"Synced {synced} subscription(s). {errors} error(s).")
    sync_with_stripe.short_description = "Sync status with Stripe"

    def fix_duplicate_active(self, request, queryset):
        """Fix users with multiple active subscriptions"""
        from django.utils import timezone
        fixed = 0

        # Group by user
        from django.db.models import Count
        users_with_multiple = (
            Subscription.objects
            .filter(status='active')
            .values('user')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        for item in users_with_multiple:
            user_id = item['user']
            subs = Subscription.objects.filter(
                user_id=user_id,
                status='active'
            ).order_by('-start_date')

            # Keep the most recent, cancel the rest
            for old_sub in subs[1:]:
                old_sub.status = 'canceled'
                old_sub.end_date = timezone.now().date()
                old_sub.save()
                fixed += 1

        self.message_user(request, f"Fixed {fixed} duplicate active subscription(s).")
    fix_duplicate_active.short_description = "Fix duplicate active subscriptions"
