from urllib.parse import urlencode
from django.utils.html import format_html
from django.contrib import admin, messages
from django.urls import reverse
from django.db.models.query import QuerySet
from django.db.models import Count
from django.templatetags.static import static

from . import models

LESS_THAN_TEN = '<10'


class InventoryFilter(admin.SimpleListFilter):

    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            (LESS_THAN_TEN, 'Low')
        ]

    def queryset(self, request, queryset: QuerySet):
        if self.value() == LESS_THAN_TEN:
            return queryset.filter(inventory__lt=10)


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    fields = ['image', 'display_thumbnail', 'default',]
    readonly_fields = ('display_thumbnail',)

    def display_thumbnail(self, instance):
        if instance.thumbnail:
            return format_html('<img src="{}" width="100" height="100" object-fit="cover" />', instance.thumbnail.url)
        return None

    display_thumbnail.allow_tags = True
    display_thumbnail.short_description = 'Thumbnail'


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ['title']
    autocomplete_fields = ['category']
    prepopulated_fields = {
        'slug': ['title']
    }
    actions = ['clear_inventory']
    list_display = ['title', 'unit_price', 'inventory',
                    'inventory_status', 'category_title', 'description', 'status']
    list_editable = ['unit_price']
    list_select_related = ['category']
    list_filter = ['category', 'last_update', InventoryFilter]
    inlines = [ProductImageInline]

    def save_related(self, request, form, formsets, change):
        product = form.instance

        super().save_related(request, form, formsets, change)

        for product_image in product.productimages.all():
            if product_image.image:
                product_image.thumbnail = product_image.make_thumbnail(
                    product_image.image)
            else:
                product_image.thumbnail = None
            product_image.save()
            return True

    @admin.display(ordering='inventory')
    def inventory_status(self, product):
        if product.inventory < 10:
            return 'Low'
        else:
            return 'Ok'

    def category_title(self, product):
        return product.category.title

    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        updated_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{updated_count} products were successfully updated.',
            messages.ERROR
        )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted=False)

    class Media:
        js = [static('custom/js/productimage-checkbox.js')]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'product_count']
    search_fields = ['title']

    @admin.display(ordering='product_count')
    def product_count(self, category):
        url = (reverse("admin:store_product_changelist")
               + '?'
               + urlencode({'category__id': str(category.id)})
               )
        return format_html("<a href='{}'>{}</a>", url, category.product_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count('products'))


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['product']
    model = models.OrderItem
    extra = 0
    min_num = 1
    max_num = 3


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    list_display = ['id', 'created_at', 'payment_status',
                    'customer', 'payment_intent', 'total_price']
    list_per_page = 10
    inlines = [OrderItemInline]


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name',
                    'phone', 'birth_date', 'order_count']
    list_per_page = 20
    list_select_related = ['user']
    ordering = ['user__first_name', 'user__last_name']
    search_fields = ['user__first_name__istartswith',
                     'user__last_name__istartswith']

    @admin.display(ordering='order_count')
    def order_count(self, customer):
        url = (reverse("admin:store_order_changelist")
               + '?'
               + urlencode({'customer__id': str(customer.id)})
               )
        return format_html("<a href='{}'>{}</a>", url, customer.order_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(order_count=Count('orders'))
