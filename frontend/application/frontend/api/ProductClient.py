# application/frontend/api/ProductClient.py
import requests
UPLOAD_FOLDER = 'application/static/images'

class ProductClient:

    @staticmethod
    def get_products():
        r = requests.get('http://192.168.0.106:5002/api/products')
        products = r.json()
        return products

    @staticmethod
    def get_product(slug):
        response = requests.request(method="GET", url='http://192.168.0.106:5002/api/product/' + slug)
        product = response.json()
        return product

    @staticmethod
    def post_product(form):
        payload = {
        'name' : form.name.data,
        'slug' : form.slug.data,
        'image' : form.image.data.filename,
        'price' : form.price.data
        }
        url = 'http://192.168.0.106:5002/api/product/create'
        requests.request("POST", url=url, data=payload)
        return {"message":"Product has been added"}