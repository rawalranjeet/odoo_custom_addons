from odoo import http
from odoo.http import request
import json

class TestController(http.Controller):
    @http.route('/shopify/webhook/products', type='json', auth='public', methods=['POST'], csrf=False)
    def shopify_webhook_products(self):
        
        data = json.loads(request.httprequest.data)

        shopify_product = request.env['shopify.products'].create({
            'name': data.get('title'),
            'price': data.get('variants',[])[0].get('price'),
            'description': data.get('body_html')
        })

        return {
            "message": "successfully created shopify product"
        }

