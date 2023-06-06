import os
import shutil
import requests
from unsplash.api import Api
from unsplash.auth import Auth
from django.core.files import File
from django.core.management.base import BaseCommand
from store.models import Product


def download_image(id):
    auth = Auth(client_id='PEGBVoUUDcvFmPANsECq9RKidCW0eGIsfu5n6O1ITMk',
                client_secret='KwhsjVrISSzdnDLeLbWCXKKvAi7IbZZEdm48zhmvJSg', redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    api = Api(auth)

    photo = api.photo.random(query='food')
    response = requests.get(photo[0].urls.raw, stream=True)

    filename = f'Image{id}.jpg'
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return filename


class Command(BaseCommand):
    help = "Command information"

    def handle(self, *args, **kwargs):
        products = Product.objects.filter(id__gt=169)
        for product in products:
            filename = download_image(product.id)
            product.image.save(os.path.basename(filename),
                               File(open(filename, 'rb')))
