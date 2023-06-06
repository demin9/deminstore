from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.files import File
from io import BytesIO
from PIL import Image
from store import permissions

from store.validators import validate_file_size


class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    DRAFT = 0
    WAITING_APPROVAL = 1
    ACTIVE = 2

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (WAITING_APPROVAL, 'Waiting approval'),
        (ACTIVE, 'Active')]

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])
    inventory = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    deleted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='productimages')
    image = models.ImageField(
        upload_to='uploads/product_images/', blank=True, null=True, validators=[validate_file_size])
    thumbnail = models.ImageField(
        upload_to='uploads/product_images/thumbnails/', blank=True, null=True)
    default = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.image}"

    def make_thumbnail(self, image, size=(300, 300)):
        img = Image.open(image)
        img = img.convert('RGB')
        img.thumbnail(size)

        thumb_io = BytesIO()
        if image.name.lower().endswith('.png'):
            img.save(thumb_io, 'PNG', quality=85)
        else:
            img.save(thumb_io, 'JPEG', quality=85)

        image_name = image.name.replace('uploads/product_images/', '')
        thumbnail = File(thumb_io, name=image_name)

        return thumbnail

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            if self.image:
                self.thumbnail = self.make_thumbnail(self.image)
                self.save()

                return self.thumbnail.url
            else:
                return '/media/uploads/product_images/default-image.jpg'


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)


class Customer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders')
    phone = models.CharField(max_length=255)
    birth_date = models.DateField(null=True)

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name

    def email(self):
        return self.user.email

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        permissions = [('view_history', 'Can view history')]


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255, null=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='addresses')

    def __str__(self) -> str:
        return f'{self.street} {self.city} {self.zip_code} {self.country}'


class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed')
    ]

    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, related_name='orders', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_intent = models.CharField(max_length=255)
    total_price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(1)], blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.customer.user.first_name} {self.customer.user.last_name}'

    def get_payment_status_display(self):
        return dict(self.PAYMENT_STATUS_CHOICES).get(self.payment_status, '')


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name='orderitems')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])


class Vendor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='vendors')
    shop_name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return f'{self.shop_name}'
