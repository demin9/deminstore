from decimal import ROUND_DOWN, Decimal
from rest_framework import serializers
from .models import Order, OrderItem, Product, Category, ProductImage, Review, Customer, Vendor


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'products_count']

    products_count = serializers.IntegerField(read_only=True)


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'shop_name', 'user']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image',
                  'thumbnail', 'default', 'get_thumbnail']

    get_thumbnail = serializers.SerializerMethodField(
        method_name='show_get_thumbnail')

    def show_get_thumbnail(self, productimage: ProductImage):
        return productimage.get_thumbnail()


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'user', 'slug', 'description', 'inventory', 'unit_price',
                  'price_with_discount', 'category', 'productimages', 'vendors']

    productimages = ProductImageSerializer(many=True, read_only=True)
    vendors = VendorSerializer(source='user.vendors', read_only=True)

    price_with_discount = serializers.SerializerMethodField(
        method_name='calculate_discount')

    def calculate_discount(self, product: Product):
        return product.unit_price - (product.unit_price * Decimal(0.20))


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'description']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id=product_id, **validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'first_name', 'last_name',
                  'email', 'birth_date', 'phone']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity', 'sub_total']

    product = ProductSerializer()

    sub_total = serializers.SerializerMethodField(
        method_name='calculate_sub_total')

    def calculate_sub_total(self, orderItem: OrderItem):
        return Decimal(orderItem.unit_price * orderItem.quantity).quantize(Decimal('0.00'), rounding=ROUND_DOWN)


class OrderSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        format='%b %d, %Y', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'payment_status',
                  'created_at', 'total_price', 'orderitems']

    orderitems = OrderItemSerializer(many=True, read_only=True)
