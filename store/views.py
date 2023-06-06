import requests
import stripe
import logging
from django.db import transaction
from django.conf import settings
from django.core.paginator import Paginator
from django.http import BadHeaderError, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, F, Prefetch, Count
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import status, permissions
from templated_mail.mail import BaseEmailMessage


from .cart import Cart
from .signals import order_created
from .pagination import DefaultPagination
from .filters import ProductFilter, ProductViewFilter
from .forms import AddressForm, CustomerForm, ReviewForm
from .models import Address, Category, Customer, Order, OrderItem, Product, ProductImage, Review
from .serializers import CategorySerializer, CustomerSerializer, OrderItemSerializer, OrderSerializer, ProductSerializer, ReviewSerializer
from .permissions import IsAdminOrReadOnly, ViewCustomerHistoryPermission

logger = logging.getLogger(__name__)


def pagination(request, object, page_Item_numbers=16):
    paginator = Paginator(object, page_Item_numbers)
    page = request.GET.get('page')
    page_objects = paginator.get_page(page)

    return page_objects


def sort_filter(request, queryset):
    sort_by = request.GET.get('sort_by')
    if sort_by:
        if sort_by == 'price_asc':
            queryset = queryset.order_by('unit_price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-unit_price')
        elif sort_by == 'title_asc':
            queryset = queryset.order_by('title')
        elif sort_by == 'title_desc':
            queryset = queryset.order_by('-title')

    product_filter = ProductFilter(request.GET, queryset=queryset)
    filtered_products = product_filter.qs.prefetch_related(Prefetch(
        'productimages', queryset=ProductImage.objects.filter(default=True)))
    page_products = pagination(request, filtered_products)
    product_count = filtered_products.count()

    filter_params = request.GET.copy()
    if 'page' in filter_params:
        del filter_params['page']
        request.GET = filter_params
        request.META['QUERY_STRING'] = filter_params.urlencode()

    context = {
        'product_filter': product_filter,
        'filtered_products': filtered_products,
        'products': page_products,
        'product_count': product_count
    }
    return context


def breadcrumb_navigation(request, label):
    breadcrumb = {'label': label, 'url': request.path}
    breadcrumbs = request.session.get('breadcrumbs', [])

    breadcrumbs = [item for item in breadcrumbs if item['label'] != label]

    breadcrumbs.append(breadcrumb)
    breadcrumbs = breadcrumbs[-4:]
    request.session['breadcrumbs'] = breadcrumbs
    return breadcrumbs


def search(request):
    try:
        logger.info('Calling search')
        query = request.GET.get('query', '')

        if query:
            request.session['search_query'] = query
        else:
            query = request.session.get('search_query', '')

        products = Product.objects.select_related('user', 'category').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')).filter(status=Product.ACTIVE, deleted=False).filter(
            Q(title__icontains=query) | Q(description__icontains=query))

        label = f'Search results for { query }'
        breadcrumbs = breadcrumb_navigation(request, label)

        context = sort_filter(request, products)
        logger.info('End of search')
    except requests.ConnectionError:
        logger.critical('search is offline')

    return render(request, 'search.html', {'query': query, 'breadcrumbs': breadcrumbs, **context})


def product_detail(request, pk):
    review_form = None

    product = get_object_or_404(
        Product.objects.select_related('user', 'category').prefetch_related('productimages').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')), pk=pk, status=Product.ACTIVE, deleted=False)

    reviews = Review.objects.filter(product_id=pk)

    breadcrumbs = breadcrumb_navigation(request, product.title)

    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.save()
            review_form = ReviewForm()
    elif request.method == 'GET':
        review_form = ReviewForm()

    context = {
        'product': product,
        'review_form': review_form,
        'breadcrumbs': breadcrumbs,
        'reviews': reviews
    }

    return render(request, 'product_detail.html', {**context})


def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = category.products.select_related('user').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')).filter(
        status=Product.ACTIVE, deleted=False)

    context = sort_filter(request, products)

    breadcrumbs = breadcrumb_navigation(request, category.title)

    return render(request, 'category_detail.html', {'category': category, 'breadcrumbs': breadcrumbs, **context})


@cache_page(5 * 60)
def all_categories(request):
    breadcrumbs = breadcrumb_navigation(request, 'All Categories')
    category = Category.objects.all()
    products = Product.objects.select_related('user').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')).filter(
        status=Product.ACTIVE, deleted=False)

    context = sort_filter(request, products)

    return render(request, 'category_detail.html', {'category': category, 'breadcrumbs': breadcrumbs, **context})


def add_to_cart(request, pk):
    cart = Cart(request)
    cart.add(pk)

    return redirect('cart')


def remove_from_cart(request, pk):
    cart = Cart(request)
    cart.remove(pk)

    return redirect('cart')


def change_quantity(request):
    product_id = int(request.POST.get('product_id', ''))
    quantity = int(request.POST.get('quantity', ''))
    cart = Cart(request)
    cart.add(product_id, quantity, True)
    return redirect('cart')


def cart_view(request):
    cart = Cart(request)
    breadcrumbs = breadcrumb_navigation(request, 'Cart')
    total_cost = 0

    if cart:
        total_cost = cart.get_total_cost()
    return render(request, 'cart_view.html', {'cart': cart, 'total_cost': total_cost, 'breadcrumbs': breadcrumbs})


def success(request):
    with transaction.atomic():
        breadcrumbs = breadcrumb_navigation(request, 'Success')

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(
            request.GET.get('session_id', ''))
        customer_id = request.session.get('customer_id')
        order_id = request.session.get('order_id')

        customer = get_object_or_404(Customer, pk=customer_id)
        order = get_object_or_404(Order, pk=order_id)

        order.payment_status = Order.PAYMENT_STATUS_COMPLETE
        order.save()
        cart = Cart(request)
        total_cost = cart.get_total_cost()

        try:
            message = BaseEmailMessage(
                template_name='emails/checkout_email.html',
                context={'customer': customer,
                         'cart': cart, 'total_cost': total_cost}
            )
            message.send([customer.user.email])
        except BadHeaderError:
            return HttpResponseBadRequest('Invalid header value')

        cart.clear()
        order_created.send_robust(request.__class__, order=order)

        return render(request, 'success.html', {'customer': customer, 'breadcrumbs': breadcrumbs})


@login_required
def checkout(request):
    breadcrumbs = breadcrumb_navigation(request, 'Checkout')

    cart = Cart(request)
    total_cost = cart.get_total_cost()
    if total_cost == 0:
        return redirect('cart')

    customer = Customer()
    address = Address()
    order = Order()
    show_customer_form = False
    show_address_form = False
    show_summary_form = False
    customer_form = None
    address_form = None

    if request.method == 'POST':
        if 'customer_form_submit' in request.POST:
            if len(Customer.objects.filter(user=request.user)) > 0:
                customer = Customer.objects.get(user=request.user)
                customer_form = CustomerForm(request.POST, instance=customer)
            else:
                customer_form = CustomerForm(request.POST)

            if customer_form.is_valid():
                customer = customer_form.save(commit=False)
                customer.user = request.user
                customer.save()

                user = User.objects.get(id=request.user.id)
                user.first_name = customer_form.cleaned_data['first_name']
                user.last_name = customer_form.cleaned_data['last_name']
                user.email = customer_form.cleaned_data['email']
                user.save()

                request.session['customer_id'] = customer.id
                show_customer_form = False
                show_address_form = True
                show_summary_form = False
                address_form = AddressForm()
            else:
                show_customer_form = True
                show_address_form = False
                show_summary_form = False
        elif 'address_form_submit' in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                customer_id = request.session.get('customer_id')
                customer = Customer.objects.get(id=customer_id)
                address.customer = customer
                address.save()

                order.customer = customer
                order.total_price = total_cost
                order.save()
                request.session['order_id'] = order.id
                for item in cart:
                    product = get_object_or_404(Product, pk=int(item['id']))
                    quantity = int(item['quantity'])
                    unit_price = float(item['unit_price'])
                    OrderItem.objects.create(
                        order=order, product=product, quantity=quantity, unit_price=unit_price)
                show_customer_form = False
                show_address_form = False
                show_summary_form = True
            else:
                show_customer_form = False
                show_address_form = True
                show_summary_form = False
        else:
            with transaction.atomic():
                line_items = []
                for item in cart:
                    product = get_object_or_404(Product, pk=int(item['id']))
                    line_items.append({
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': product.title,
                            },
                            'unit_amount': int(product.unit_price * 100),
                        },
                        'quantity': int(item['quantity'])
                    })

                stripe.api_key = settings.STRIPE_SECRET_KEY
                session = stripe.checkout.Session.create(
                    line_items=line_items,
                    payment_method_types=['card'],
                    mode='payment',
                    success_url=f'{settings.WEBSITE_URL}' +
                    "cart/success?session_id={CHECKOUT_SESSION_ID}",
                    cancel_url=f'{settings.WEBSITE_URL}/cart'
                )

                show_customer_form = False
                show_address_form = False
                show_summary_form = False
                return JsonResponse({'session': session})
    else:
        show_customer_form = True
        show_address_form = False
        show_summary_form = False

        if len(Customer.objects.filter(user=request.user)) > 0:
            customer = Customer.objects.get(user=request.user)
        else:
            customer.user = request.user

        customer_form = CustomerForm(instance=customer)
        address_form = AddressForm()

    context = {
        'customer_form': customer_form,
        'address_form': address_form,
        'show_customer_form': show_customer_form,
        'show_address_form': show_address_form,
        'show_summary_form': show_summary_form,
        'cart': cart,
        'total_cost': total_cost,
        'address': address,
        'pub_key': settings.STRIPE_PUB_KEY
    }

    return render(request, 'checkout.html', {'breadcrumbs': breadcrumbs, **context})


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(category_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Category can not be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductViewFilter
    pagination_class = DefaultPagination
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Product.objects.select_related('user', 'category').prefetch_related('productimages', 'user__vendors')

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Product can not be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.get(
            user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options', 'delete']
    renderer_classes = [TemplateHTMLRenderer]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.select_related('customer').all(
            ).prefetch_related(
                'orderitems__product__user__vendors',
                Prefetch(
                    'orderitems__product__productimages', queryset=ProductImage.objects.filter(default=True))
            )
        else:
            return Order.objects.select_related('customer').filter(
                customer__user_id=user
            ).prefetch_related(
                'orderitems__product__user__vendors',
                Prefetch(
                    'orderitems__product__productimages', queryset=ProductImage.objects.filter(default=True))
            )

    def list(self, request, *args, **kwargs):
        breadcrumbs = breadcrumb_navigation(request, 'My Orders')

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        orders = serializer.data
        if request.accepted_renderer.format == 'html':
            return render(request, 'myorders.html', {'orders': orders, 'breadcrumbs': breadcrumbs})

        return Response(orders)


class OrderItemViewSet(ModelViewSet):
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        return OrderItem.objects.filter(order_id=self.kwargs['order_pk'])

    def get_serializer_context(self):
        return {'order_id': self.kwargs['order_pk']}
