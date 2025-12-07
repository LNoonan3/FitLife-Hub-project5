from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order, OrderItem, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'stock_status')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    list_editable = ('price', 'stock')
    ordering = ('-created_at',)
    
    def stock_status(self, obj):
        if obj.stock == 0:
            color = 'red'
            text = 'Out of Stock'
        elif obj.stock < 10:
            color = 'orange'
            text = 'Low Stock'
        else:
            color = 'green'
            text = 'In Stock'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    stock_status.short_description = 'Stock Status'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'line_total')
    can_delete = False
    
    def line_total(self, obj):
        return f"€{obj.quantity * obj.unit_price:.2f}"
    line_total.short_description = 'Line Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_display', 'status', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('created_at', 'updated_at', 'total_display')
    list_editable = ('status',)
    ordering = ('-created_at',)
    
    def total_display(self, obj):
        return f"€{obj.total_cents / 100:.2f}"
    total_display.short_description = 'Total'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'rating_stars', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = 'Stars'