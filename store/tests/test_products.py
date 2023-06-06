from rest_framework import status
from model_bakery import baker
from django.contrib.auth.models import User
from decimal import Decimal
import pytest

from store.models import Category, Order, OrderItem, Product


@pytest.fixture
def create_product(api_client):
    def _create_product(product):
        return api_client.post('/products/', product)
    return _create_product


@pytest.fixture
def get_product(api_client):
    def _get_product(product_id):
        return api_client.get(f'/products/{product_id}/')
    return _get_product


@pytest.fixture
def update_product(api_client):
    def _update_product(product_id, updated_data):
        return api_client.put(f'/products/{product_id}/', updated_data, partial=True)
    return _update_product


@pytest.fixture
def delete_product(api_client):
    def _delete_product(product_id):
        return api_client.delete(f'/products/{product_id}/')
    return _delete_product


@pytest.mark.django_db
class TestCreateProduct:
    def test_if_user_is_anonymous_returns_401(self, create_product):
        response = create_product({})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, create_product, authenticate):
        authenticate()

        response = create_product({})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_data_is_valid_returns_201(self, create_product, authenticate):
        authenticate(is_staff=True)
        category = baker.make(Category)
        user = baker.make(User)

        product_data = {
            'category': category.id,
            'user': user.id,
            'title': 'Test Product',
            'slug': 'test-product',
            'description': 'This is a test product',
            'unit_price': 9.99,
            'inventory': 10
        }

        response = create_product(product_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0

    def test_if_data_is_invalid_returns_400(self, create_product, authenticate):
        authenticate(is_staff=True)
        category = baker.make(Category)
        user = baker.make(User)

        product_data = {
            'category': category.id,
            'user': user.id,
            'title': '',
            'slug': 'test-product',
            'description': 'This is a test product',
            'unit_price': 9.99,
            'inventory': 10
        }

        response = create_product(product_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['title'] is not None


@pytest.mark.django_db
class TestRetrieveProduct:
    def test_if_product_exists_returns_200(self, get_product):
        product = baker.make(Product)

        response = get_product(product.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': product.id,
            'category': product.category.id,
            'user': product.user.id,
            'title': product.title,
            'slug': product.slug,
            'description': product.description,
            'unit_price': product.unit_price,
            'inventory': product.inventory,
            'price_with_discount': product.unit_price - (product.unit_price * Decimal(0.20)),
            'productimages': [],
            'vendors': None
        }

    def test_if_product_does_not_exists_returns_404(self, get_product):
        response = get_product(999999)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUpdateProduct:
    def test_if_user_is_anonymous_returns_401(self, update_product):
        product = baker.make(Product)
        updated_data = {
            'category': product.category.id,
            'user': product.user.id,
            'title': 'New Title',
            'slug': product.slug,
            'description': '',
            'unit_price': product.unit_price,
            'inventory': product.inventory
        }

        response = update_product(product.id, updated_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, update_product, authenticate):
        authenticate()
        product = baker.make(Product)
        updated_data = {
            'category': product.category.id,
            'user': product.user.id,
            'title': 'New Title',
            'slug': product.slug,
            'description': '',
            'unit_price': product.unit_price,
            'inventory': product.inventory
        }

        response = update_product(product.id, updated_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_product_exists_and_data_is_valid_returns_200(self, update_product, authenticate):
        authenticate(is_staff=True)
        product = baker.make(Product)

        updated_data = {
            'category': product.category.id,
            'user': product.user.id,
            'title': 'New Title',
            'slug': product.slug,
            'description': '',
            'unit_price': product.unit_price,
            'inventory': product.inventory
        }

        response = update_product(product.id, updated_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'New Title'


@pytest.mark.django_db
class TestDeleteproduct:
    def test_if_user_is_anonymous_returns_401(self, delete_product):
        product = baker.make(Product)

        response = delete_product(product.id)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, delete_product, authenticate):
        authenticate()
        product = baker.make(Product)

        response = delete_product(product.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_product_exists_with_orderitems_returns_405(self, delete_product, authenticate):
        authenticate(is_staff=True)
        product = baker.make(Product)
        order = baker.make(Order)
        orderitem = baker.make(OrderItem, order=order,
                               product=product, _quantity=2)

        response = delete_product(product.id)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_if_product_exists_without_orderitems_returns_204(self, delete_product, authenticate):
        authenticate(is_staff=True)
        product = baker.make(Product)

        response = delete_product(product.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_product_does_not_exist_returns_404(self, delete_product, authenticate):
        authenticate(is_staff=True)

        response = delete_product(99999)

        assert response.status_code == status.HTTP_404_NOT_FOUND
