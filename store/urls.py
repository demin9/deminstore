from django.urls import include, path
from rest_framework_nested import routers

from .views import CategoryViewSet, CustomerViewSet, ProductViewSet, ReviewViewSet, add_to_cart, all_categories, cart_view, checkout, product_detail, category_detail, remove_from_cart, search, change_quantity, success

router = routers.SimpleRouter()
router.register('categories', CategoryViewSet)
router.register('products', ProductViewSet, basename='products')
products_router = routers.NestedSimpleRouter(
    router, 'products', lookup='product')
products_router.register('reviews', ReviewViewSet, basename='product-reviews')
router.register('customers', CustomerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)),
    path('search/', search, name='search'),
    path('add_to_cart/<int:pk>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<str:pk>/', remove_from_cart, name='remove_from_cart'),
    path('cart/', cart_view, name='cart'),
    path('cart/checkout/', checkout, name='checkout'),
    path('cart/success/', success, name='success'),
    path('change_quantity/', change_quantity, name='change_quantity'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('all_categories/', all_categories, name='all_categories'),
    path('category/<int:pk>/', category_detail, name='category_detail'),
]
