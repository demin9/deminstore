from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.db.models.aggregates import Count
from django.db.models import F

from store.models import OrderItem, Product
from store.views import breadcrumb_navigation, sort_filter
from .forms import ContactForm


def contact(request):
    breadcrumbs = breadcrumb_navigation(request, 'Contact')
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                message = form.cleaned_data['message']
                send_mail(
                    'Message from DeminStore',
                    'Name: {}\nEmail: {}\n\n{}'.format(name, email, message),
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
            except BadHeaderError:
                return HttpResponseBadRequest('Invalid header value')

            return render(request, 'contact/thanks.html')
    else:
        form = ContactForm()
    return render(request, 'contact/contact.html', {'form': form, 'breadcrumbs': breadcrumbs})


def frontpage(request):
    if request.session.get('breadcrumbs'):
        del request.session['breadcrumbs']

    order_item_ids = OrderItem.objects.values('product_id').annotate(
        count=Count('product_id')).order_by('-count')[:16]
    product_ids = [o['product_id'] for o in order_item_ids]

    popular_products = Product.objects.select_related('user', 'category').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')).filter(
        status=Product.ACTIVE, deleted=False, id__in=product_ids)

    context = sort_filter(request, popular_products)

    return render(request, 'frontpage.html', {**context})


def aboutpage(request):
    breadcrumbs = breadcrumb_navigation(request, 'About Us')
    return render(request, 'about.html', {'breadcrumbs': breadcrumbs})
