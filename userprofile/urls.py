from django.urls import path
from django.contrib.auth import views as auth_views

from store.views import OrderViewSet
from .views import add_product, change_email, change_password, delete_product, edit_product, myaccount, myprofile, mystore, vendor, vendor_detail


urlpatterns = [
    path('vendor/', vendor, name='vendor'),
    path('vendor_detail/<int:pk>/', vendor_detail, name='vendor_detail'),
    path('myaccount/', myaccount, name='myaccount'),
    path('mystore/', mystore, name='mystore'),
    path('mystore/add_product/', add_product, name='add_product'),
    path('mystore/edit_product/<int:pk>/', edit_product, name='edit_product'),
    path('mystore/delete_product/<int:pk>/',
         delete_product, name='delete_product'),
    path('myprofile/', myprofile, name='myprofile'),
    path('myorders/',
         OrderViewSet.as_view({'get': 'list'}), name='myorders'),
    path('change_password/', change_password, name='change_password'),
    path('change_email/', change_email, name='change_email'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout')
]
