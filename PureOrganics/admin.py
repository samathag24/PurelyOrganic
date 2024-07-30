from django.contrib import admin
from .models import Category, Product, Brand, Order, OrderItem, FAQ
from django.utils.safestring import mark_safe
from .models import UserVisit

# Customizing the admin interface for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'total')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'orderitem__product__name')
    readonly_fields = ('created_at', 'total')

    def total(self, obj):
        return obj.total
    total.admin_order_field = 'total'

# Customizing the admin interface for Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'image_tag')
    search_fields = ('name', 'description')

    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="%s" style="max-height: 100px; max-width: 100px;" />' % obj.image.url)
        return '(No image)'

    image_tag.short_description = 'Image Preview'

# Customizing the admin interface for Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'image_tag')
    search_fields = ('name', 'description', 'category__name', 'brand__name')
    list_filter = ('category', 'brand', 'available')
    ordering = ('-created_at',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="%s" style="max-height: 100px; max-width: 100px;" />' % obj.image.url)
        return '(No image)'

    image_tag.short_description = 'Image Preview'

# Customizing the admin interface for Brand
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

# Register OrderItem if you need to manage it directly from the admin interface
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')
    search_fields = ('order__user__username', 'product__name')
    list_filter = ('order',)

# Uncomment if you need to register Cart and CartItem separately
# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user',)
#     search_fields = ('user__username',)

# @admin.register(CartItem)
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'product', 'quantity')
#     search_fields = ('cart__user__username', 'product__name')
#     list_filter = ('cart',)

@admin.register(UserVisit)
class UserVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'visit_count', 'last_visit')
    list_filter = ('user', 'last_visit')
    search_fields = ('user__username',)


admin.site.register(FAQ)