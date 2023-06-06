from decimal import ROUND_DOWN, Decimal
from django.conf import settings
from django.db.models import Prefetch
from store.models import Product, ProductImage


class Cart(object):
    def __init__(self, request):
        self.session = request.session

        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def __iter__(self):
        for item in self.cart.values():
            item['total_price'] = item['unit_price'] * item['quantity']
            item['total_price'] = Decimal(item['total_price']).quantize(
                Decimal('0.00'), rounding=ROUND_DOWN)
            item['total_price'] = str(item['total_price'])
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def add(self, product_id, quantity=1, update_quantity=False):
        product = Product.objects.prefetch_related(
            Prefetch(
                'productimages', queryset=ProductImage.objects.filter(default=True))).get(pk=product_id)
        product_id = str(product_id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'id': int(product.id),
                'quantity': int(quantity),
                'title': str(product.title),
                'unit_price': float(product.unit_price),
                'inventory': int(product.inventory),
                'description': str(product.description),
                'get_thumbnail': [str(product_image.get_thumbnail()) for product_image in product.productimages.all()],
                'category_id': int(product.category.id)
            }
        else:
            update_quantity = True

        if update_quantity:
            self.cart[product_id]['quantity'] = int(quantity)

        self.save()

    def remove(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]

            self.save()

    def get_total_cost(self):
        return sum([Decimal(item['total_price']) for item in self]).quantize(
            Decimal('0.00'), rounding=ROUND_DOWN)

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
