from odoo import fields, api,_, models
from odoo.exceptions import UserError
import requests


class ShopifyWebhooks(models.Model):
    _name = "shopify.webhooks"
    _description = "Shopify Webhook"

    name = fields.Char("Name", required=True)
    store_id = fields.Many2one('shopify.store', string="Store", required=True)
    # address = fields.Char("Address" ,required=True)
    topic = fields.Selection([('products/create','Products Create')], string="Topic", required=True)
    shopify_webhook_id = fields.Char("Shopify Webhook Id")


    def action_create_webhook(self):
        
        url = f'https://{self.store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/webhooks.json'
        address = f'{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/shopify/webhook/products'

        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.store_id.shopify_access_token
        }

        payload = {
            'webhook':{
                "address" : address,
                "topic" : self.topic,
                "format" : "json",
            }
        }

        try:
            
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 201:
                self.write({
                    'shopify_webhook_id': response.json().get("webhook", {}).get("id")
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Webhook Success'),
                        'message': _('webhook created'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Webhook Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }

        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
        

    
    def action_delete_webhook(self):
        
        url = f'https://{self.store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/webhooks/{self.shopify_webhook_id}.json'

        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.store_id.shopify_access_token
        }

        try:
            
            response = requests.delete(url, headers=headers)

            if response.status_code == 200:
                self.write({
                    'shopify_webhook_id': ""
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Webhook Success'),
                        'message': _('Webhook Deleted'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Webhook Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }

        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
        

    
            