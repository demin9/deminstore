from random import randint
from django.http import HttpRequest
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task(2)
    def view_products(self):
        category_id = randint(2, 10)
        self.client.get(
            f'/products/?category_id={category_id}', name='/products/')

    @task(4)
    def view_product(self):
        product_id = randint(1, 219)
        self.client.get(
            f'/products/{product_id}', name='/products/:id')

    @task
    def view_all_categories(self):
        self.client.get('/all_categories/')
