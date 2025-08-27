from odoo import fields, api, models,_
from werkzeug import urls
from odoo.exceptions import UserError
import requests


class ShopifyStore(models.Model):
    _name = "shopify.store"
    _description = "Shopify Store"

    name = fields.Char("Name", required=True)
    shopify_store_name = fields.Char("Shopify Store Name", required=True)
    shopify_access_token = fields.Char("Shopify Access Token", required=True)

    # Credentials testing function
    def action_test_connection(self):
        url = f'https://{self.shopify_store_name}.myshopify.com/admin/api/2025-07/shop.json'
        
        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.shopify_access_token
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Connection Success'),
                        'message': _('Everything is Good'),
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