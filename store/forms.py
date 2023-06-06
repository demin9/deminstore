from django import forms

from .models import Address, Customer, Product, ProductImage, Review, Vendor


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('image', 'thumbnail', 'default', )


ProductImageFormSet = forms.inlineformset_factory(
    parent_model=Product,
    model=ProductImage,
    form=ProductImageForm,
    fields=('image', 'thumbnail', 'default', ),
    extra=0,
    can_delete=True,
)


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('category', 'title', 'description',
                  'unit_price', 'inventory', 'status')
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'inventory': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'})
        }


class CustomerForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}),
        input_formats=['%Y-%m-%d']
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'email', 'phone', 'birth_date')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            initial = kwargs.get('initial', {})
            initial['first_name'] = instance.user.first_name
            initial['last_name'] = instance.user.last_name
            initial['email'] = instance.user.email
            initial['phone'] = instance.phone
            initial['birth_date'] = instance.birth_date
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('street', 'city', 'country', 'zip_code')
        widgets = {
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'})
        }


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ('shop_name', )
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control'})
        }
