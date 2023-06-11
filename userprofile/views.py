from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from store.models import Product, OrderItem, Vendor, Order, ProductImage
from store.views import breadcrumb_navigation, pagination, sort_filter
from store.forms import ProductForm, ProductImageFormSet, VendorForm
from .models import Userprofile
from .forms import ChangeEmailForm, UserCreationForm


@login_required
def mystore(request):
    breadcrumbs = breadcrumb_navigation(request, 'My Store')

    products = request.user.products.exclude(deleted=True)
    context = sort_filter(request, products)

    order_items = OrderItem.objects.select_related(
        'product').select_related('order__customer').filter(product__user=request.user)

    total_earnings = 0
    total_earnings = sum(
        [order_item.unit_price * order_item.quantity for order_item in order_items if order_item.order.payment_status == Order.PAYMENT_STATUS_COMPLETE])

    try:
        if request.user.userprofile.is_vendor:
            vendor = get_object_or_404(Vendor, user_id=request.user.id)
        else:
            vendor = None
    except Http404:
        vendor = None

    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)

        if form.is_valid():
            if vendor:
                vendor = form.save()
            else:
                vendor = form.save(commit=False)
                vendor.user = request.user
                vendor.save()

    else:
        form = VendorForm(instance=vendor)

    return render(request, 'mystore.html', {'order_items': order_items, 'total_earnings': total_earnings, 'form': form, 'breadcrumbs': breadcrumbs, **context})


@login_required
def add_product(request):
    page_title = 'Add product'
    breadcrumbs = breadcrumb_navigation(request, page_title)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductImageFormSet(
            request.POST, request.FILES)

        if form.is_valid():
            title = request.POST.get('title')
            product = form.save(commit=False)
            product.user = request.user
            product.slug = slugify(title)
            product.save()

            if formset.is_valid():
                for index, form in enumerate(formset.forms):
                    if form.has_changed():
                        productimage = form.save(commit=False)
                        productimage.product = product
                        productimage.thumbnail = productimage.make_thumbnail(
                            form.cleaned_data['image'])
                        productimage.save()

                    delete_key = f"productimages-{index}-delete"
                    if delete_key in request.POST:
                        productimage = form.instance
                        productimage.image.delete(save=False)
                        productimage.thumbnail.delete(save=False)
                        productimage.delete()

                for key in request.FILES.keys():
                    if key.startswith('productimages-'):
                        new_image_file = request.FILES[key]
                        productimage = ProductImage(
                            product=product,
                            image=new_image_file,
                        )
                        productimage.thumbnail = productimage.make_thumbnail(
                            new_image_file)

                        index = key.split('-')[1]
                        default_checkbox_name = f'productimages-{ index }-default'
                        default_value = request.POST.get(default_checkbox_name)
                        if default_value == 'on':
                            productimage.default = True
                        else:
                            productimage.default = False

                        productimage.save()

                        delete_key = f"productimages-{index}-delete"
                        if delete_key in request.POST:
                            productimage.image.delete(save=False)
                            productimage.thumbnail.delete(save=False)
                            productimage.delete()

                formset.save()

                messages.success(
                    request, f'The product {product.title} was changed successfully.')
                return redirect('mystore')
            else:
                formset_errors = formset.errors
                for form_errors in formset_errors:
                    for field, error_msgs in form_errors.items():
                        for error_msg in error_msgs:
                            messages.error(
                                request, f'Error: {error_msg}')
    else:
        form = ProductForm()
        formset = ProductImageFormSet()

    form_index = formset.total_form_count()
    form_count = 6 - formset.total_form_count()

    context = {
        'form': form,
        'formset': formset,
        'form_count': form_count,
        'form_index': form_index
    }

    return render(request, 'product_form.html', {'title': page_title, 'breadcrumbs': breadcrumbs, **context})


@login_required
def edit_product(request, pk):
    page_title = 'Edit product'
    breadcrumbs = breadcrumb_navigation(request, page_title)

    product = Product.objects.prefetch_related(
        'productimages').filter(user=request.user).get(pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            product = form.save()
            formset = ProductImageFormSet(
                request.POST, request.FILES, instance=product)

            if formset.is_valid():
                for index, form in enumerate(formset.forms):
                    if form.has_changed():
                        productimage = form.save(commit=False)
                        productimage.product = product
                        productimage.thumbnail = productimage.make_thumbnail(
                            form.cleaned_data['image'])
                        productimage.save()

                    delete_key = f"productimages-{index}-delete"
                    if delete_key in request.POST:
                        productimage = form.instance
                        productimage.image.delete(save=False)
                        productimage.thumbnail.delete(save=False)
                        productimage.delete()

                for key in request.FILES.keys():
                    if key.startswith('productimages-'):
                        new_image_file = request.FILES[key]
                        productimage = ProductImage(
                            product=product,
                            image=new_image_file,
                        )
                        productimage.thumbnail = productimage.make_thumbnail(
                            new_image_file)

                        index = key.split('-')[1]
                        default_checkbox_name = f'productimages-{ index }-default'
                        default_value = request.POST.get(default_checkbox_name)
                        if default_value == 'on':
                            productimage.default = True
                        else:
                            productimage.default = False

                        productimage.save()

                        delete_key = f"productimages-{index}-delete"
                        if delete_key in request.POST:
                            productimage.image.delete(save=False)
                            productimage.thumbnail.delete(save=False)
                            productimage.delete()

                formset.save()

                messages.success(
                    request, f'The product {product.title} was changed successfully.')
                return redirect('mystore')
            else:
                formset_errors = formset.errors
                for form_errors in formset_errors:
                    for field, error_msgs in form_errors.items():
                        for error_msg in error_msgs:
                            messages.error(
                                request, f'Error: {error_msg}')

    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)

    form_index = formset.total_form_count()
    form_count = 6 - formset.total_form_count()

    context = {
        'form': form,
        'formset': formset,
        'form_count': form_count,
        'form_index': form_index
    }

    return render(request, 'product_form.html', {'title': page_title, 'product': product, 'breadcrumbs': breadcrumbs, **context})


@login_required
def delete_product(request, pk):
    product = Product.objects.filter(user=request.user).get(pk=pk)
    product.deleted = True
    product.save()
    messages.success(
        request, f'The product {product.title} was deleted successfully.')
    return redirect('mystore')


def myaccount(request):
    breadcrumbs = breadcrumb_navigation(request, 'My Account')

    signup_form = UserCreationForm()
    login_form = AuthenticationForm()
    next_url = ''

    if request.method == 'POST':
        if 'login_form_submit' in request.POST:
            login_form = AuthenticationForm(request, request.POST)

            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)

                next_url = request.POST.get('next')
                if next_url is not None and next_url != 'None' and next_url != '':
                    return redirect(next_url)
                else:
                    return redirect('frontpage')
        else:
            signup_form = UserCreationForm(request.POST)

            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)

                userprofile = Userprofile.objects.create(user=user)

                next_url = request.POST.get('next')
                if next_url is not None and next_url != 'None' and next_url != '':
                    return redirect(next_url)
                else:
                    return redirect('frontpage')
    else:
        next_url = request.GET.get('next')
        login_form = AuthenticationForm()
        signup_form = UserCreationForm()

    return render(request, 'myaccount.html', {'signup_form': signup_form, 'login_form': login_form, 'next_url': next_url, 'breadcrumbs': breadcrumbs})


def vendor_detail(request, pk):
    user = get_object_or_404(User.objects.annotate(vendor_userid=F('vendors'), vendor_shop_name=F('vendors__shop_name')).prefetch_related(Prefetch(
        'products', queryset=Product.objects.select_related('category').annotate(vendor_userid=F('user__vendors'), vendor_shop_name=F('user__vendors__shop_name')).filter(status=Product.ACTIVE, deleted=False))), pk=pk)
    products = user.products.all()

    context = sort_filter(request, products)
    breadcrumbs = breadcrumb_navigation(request, user.vendor_shop_name)

    return render(request, 'vendor_detail.html', {'user': user, 'breadcrumbs': breadcrumbs, **context})


@login_required
def myprofile(request):
    breadcrumbs = breadcrumb_navigation(request, 'My Profile')
    return render(request, 'myprofile.html', {'breadcrumbs': breadcrumbs})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect('myprofile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'myprofile.html', {'form': form})


@login_required
def change_email(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your email was successfully updated!')
            return redirect('myprofile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ChangeEmailForm(instance=request.user)
    return render(request, 'myprofile.html', {'form': form})


@login_required
def vendor(request):
    breadcrumbs = breadcrumb_navigation(request, 'Become a Vendor')

    user = request.user
    if request.method == 'POST':
        form = VendorForm(request.POST)

        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = user
            vendor.save()
            try:
                userprofile = get_object_or_404(Userprofile, user_id=user.id)
                userprofile.is_vendor = True
                userprofile.save()
            except Http404:
                userprofile = Userprofile.objects.create(
                    user_id=user.id, is_vendor=True)
            return redirect('mystore')
    else:
        form = VendorForm()

    return render(request, 'vendor.html', {'form': form, 'breadcrumbs': breadcrumbs})
