from odoo import http
from odoo.http import request
import json

class TestController(http.Controller):
    @http.route('/shopify/webhook/products', type='json', auth='public', methods=['POST'], csrf=False)
    def shopify_webhook_products(self):
        return

        data = json.loads(request.httprequest.data)

        if not data:
            return {
                "status": 400,
                "message": "required data is missing"
            }

        product = request.env['product.template'].create({
            'shopify_product_id': data.get('id'),
             
            'name': data.get('title'),
            'description': data.get('body_html')
        })

        return {
            "message": "successfully created shopify product"
        }

