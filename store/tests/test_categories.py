from rest_framework import status
from model_bakery import baker
import pytest

from store.models import Category, Product


@pytest.fixture
def create_category(api_client):
    def _create_category(category):
        return api_client.post('/categories/', category)
    return _create_category


@pytest.fixture
def get_category(api_client):
    def _get_category(category_id):
        return api_client.get(f'/categories/{category_id}/')
    return _get_category


@pytest.fixture
def update_category(api_client):
    def _update_category(category_id, new_title):
        return api_client.put(f'/categories/{category_id}/', {'title': new_title})
    return _update_category


@pytest.fixture
def delete_category(api_client):
    def _delete_category(category_id):
        return api_client.delete(f'/categories/{category_id}/')
    return _delete_category


@pytest.mark.django_db
class TestCreateCategory:
    def test_if_user_is_anonymous_returns_401(self, create_category):
        # Arrange

        # Act
        response = create_category({'title': 'a'})

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, create_category, authenticate):
        authenticate()

        response = create_category({'title': 'a'})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_data_is_invalid_returns_400(self, create_category, authenticate):
        authenticate(is_staff=True)

        response = create_category({'title': ''})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['title'] is not None

    def test_if_data_is_valid_returns_201(self, create_category, authenticate):
        authenticate(is_staff=True)

        response = create_category({'title': 'a'})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0


@pytest.mark.django_db
class TestRetrieveCategory:
    def test_if_category_exists_returns_200(self, get_category):
        category = baker.make(Category)

        response = get_category(category.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'id': category.id,
            'title': category.title,
            'products_count': 0
        }

    def test_if_category_does_not_exists_returns_404(self, get_category):
        response = get_category(999)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_if_category_has_associated_products_returns_products_count(self, get_category):
        category = baker.make(Category)
        baker.make(Product, category=category, _quantity=10)

        response = get_category(category.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['products_count'] == 10


@pytest.mark.django_db
class TestUpdateCategory:
    def test_if_user_is_anonymous_returns_401(self, update_category):
        category = baker.make(Category)

        response = update_category(category.id, 'New Title')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, update_category, authenticate):
        authenticate()
        category = baker.make(Category)

        response = update_category(category.id, 'New Title')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_category_exists_and_data_is_valid_returns_200(self, update_category, authenticate):
        authenticate(is_staff=True)
        category = baker.make(Category)

        response = update_category(category.id, 'New Title')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'New Title'


@pytest.mark.django_db
class TestDeleteCategory:
    def test_if_user_is_anonymous_returns_401(self, delete_category):
        category = baker.make(Category)

        response = delete_category(category.id)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_not_admin_returns_403(self, delete_category, authenticate):
        authenticate()
        category = baker.make(Category)

        response = delete_category(category.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_if_category_exists_returns_204(self, delete_category, authenticate):
        authenticate(is_staff=True)
        category = baker.make(Category)

        response = delete_category(category.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_category_does_not_exist_returns_404(self, delete_category, authenticate):
        authenticate(is_staff=True)

        response = delete_category(999)

        assert response.status_code == status.HTTP_404_NOT_FOUND
