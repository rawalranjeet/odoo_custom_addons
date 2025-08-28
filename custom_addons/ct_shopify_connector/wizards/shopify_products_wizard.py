from odoo import _,api, models, fields
from odoo.exceptions import UserError
import requests


class ShopifyProductsWizard(models.TransientModel):
    _name = "shopify.products.wizard"

    shopify_store_id = fields.Many2one("shopify.store", required=True)

    def action_get_products(self):
        url = f'https://{self.shopify_store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/products.json'
        
        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.shopify_store_id.shopify_access_token
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:

                shopify_products = response.json().get('products')
                total_product_fetched = 0

                for product in shopify_products:
                    product_template = self.env['product.template'].search([('shopify_product_id','=',product.get('id'))])
                    total_product_fetched+=1

                    if not product_template:
                        vals = {
                            'shopify_product_id': product.get('id'),
                            'shopify_store_id': self.shopify_store_id.id,
                            'name': product.get('title'),
                            'description': product.get('body_html'),
                        }

                        product_template = self.env['product.template'].create(vals)

                    shopify_products_variant = product.get('variants')

                    for varient in shopify_products_variant:

                        product_product = self.env['product.product'].search([('shopify_product_variant_id','=',varient.get('id'))])

                        if not product_product:

                            vals = {
                                'shopify_product_variant_id': varient.get('id'),
                                'shopify_store_id': self.shopify_store_id.id,
                                'name': varient.get('title'),
                                'lst_price': varient.get('price'),
                                'default_code'
                            }
                        
                            product_product = self.env['product.product'].create(vals)
                
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Shopify Customer Success'),
                            'message': _(f'Customer Fetched, {total_product_fetched} in total'),
                            'type': 'success',
                            'sticky': False,
                        },
                    }

            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Connection Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }
        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
