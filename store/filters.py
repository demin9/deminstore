import django_filters
from django_filters.rest_framework import FilterSet
from .models import Vendor, Product


class ProductViewFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            'user_id': ['exact'],
            'category_id': ['exact'],
            'unit_price': ['gt', 'lt']
        }


class ProductFilter(django_filters.FilterSet):
    VENDOR_CHOICES = [(vendor.id, vendor.shop_name)
                      for vendor in Vendor.objects.all()]

    PRICE_CHOICES = [
        ('', 'Price Range'),
        ('0-50', 'Under $50'),
        ('50-100', '$50 - $100'),
        ('100-250', '$100 - $250'),
        ('250-500', '$250 - $500'),
        ('500-1000', '$500 - $1000'),
        ('1000-', '$1000 and above')
    ]

    SORT_CHOICES = (
        ('', 'Sort by'),
        ('price_asc', 'Price: Low to High'),
        ('price_desc', 'Price: High to Low'),
        ('title_asc', 'Product Title: A to Z'),
        ('title_desc', 'Product Title: Z to A'),
    )

    vendor = django_filters.MultipleChoiceFilter(
        field_name='user__vendors__id', choices=VENDOR_CHOICES)

    unit_price = django_filters.MultipleChoiceFilter(
        field_name='unit_price', choices=PRICE_CHOICES, method='filter_by_price_range')

    status = django_filters.MultipleChoiceFilter(
        field_name='status', choices=Product.STATUS_CHOICES)

    title = django_filters.CharFilter(
        field_name='title', lookup_expr='icontains')

    def filter_by_price_range(self, queryset, name, value):
        if value[0]:
            min_price, max_price = value[0].split('-')
            if max_price != '':
                return queryset.filter(unit_price__gte=min_price, unit_price__lte=max_price)
            else:
                return queryset.filter(unit_price__gte=min_price)
        return queryset

    class Meta:
        model = Product
        fields = ['vendor', 'unit_price', 'status', 'title']
