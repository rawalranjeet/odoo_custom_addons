from odoo import fields, api, models,_
from werkzeug import urls
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class ShopifyStore(models.Model):
    _name = "shopify.store"
    _description = "Shopify Store"

    name = fields.Char("Name", required=True)
    shopify_store_name = fields.Char("Shopify Store Name", required=True)
    shopify_access_token = fields.Char("Shopify Access Token", required=True)
    state = fields.Selection([('draft','Draft'),('connected','Connected'),('failed','Failed')], default='draft')
    currency_id = fields.Many2one('res.currency')

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

                currency_name = response.json().get('shop', {}).get('currency')

                res_currency = self.env['res.currency'].search([('name','=',currency_name)])

                if not res_currency:
                    self.write({
                        'state':'failed'
                    })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Shopify Connection Failed'),
                            'message': f'Currency: {currency_name} is not found in Odoo, Please Activate it first',
                            'type': 'danger',
                            'sticky': False,
                        },
                    }
                


                self.write({
                    'state':'connected',
                    'currency_id': res_currency.id,
                })

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
                self.write({
                    'state':'failed'
                })

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
        

    def action_disconnect(self):
        self.write({
                    'state':'draft'
                })
        
    def action_get_customers_all(self):
        
        shopify_stores = self.env['shopify.store'].search([])
        
        for store in shopify_stores:
            if store.state == 'connected':

                url = f'https://{store.shopify_store_name}.myshopify.com/admin/api/2025-07/customers.json'
        
                headers = {
                    'Content-Type':'application/json',
                    'X-Shopify-Access-Token': store.shopify_access_token
                }

                try:
                    response = requests.get(url, headers=headers)

                    if response.status_code == 200:

                        customers = response.json().get('customers')
                        total_customer_fetched = 0

                        for customer in customers:
                            # search if already exists
                            partner = self.env['res.partner'].search([('shopify_customer_id', '=', customer.get('id'))])
                            total_customer_fetched += 1;

                            if not partner:
                                vals = {
                                    'shopify_customer_id':customer.get('id'),
                                    'shopify_store_id': store.id,
                                    'name' : customer.get('first_name') +" "+ customer.get('last_name'),
                                    'email': customer.get('email'),
                                    'phone': customer.get('phone'),
                                }

                                partner = self.env['res.partner'].create(vals)

                            addresses = customer.get('addresses')

                            for address in addresses:
                                child_partner = self.env['res.partner'].search([('shopify_customer_id', '=', address.get('id'))])

                                if not child_partner:
                                    country = self.env['res.country'].search([('code','=',address.get('country_code'))])

                                    vals = {
                                        'shopify_customer_id':address.get('id'),
                                        'shopify_store_id': store.id,
                                        'name' : address.get('first_name') +" "+ address.get('last_name'),
                                        'phone': address.get('phone'),
                                        'parent_id': partner.id,
                                        'street': address.get('address1'),
                                        'street2': address.get('address2'),
                                        'zip': address.get('zip'),
                                        'country_code': address.get('country_code'),
                                        'country_id': country.id if country else 233,
                                        'city': address.get('city'),
                                        'type': 'other'
                                    }

                                    child_partner = self.env['res.partner'].create(vals)
                                

                        _logger.info(f"{total_customer_fetched} customers imported from the Store {store.name}")

                        
                    else:
                        _logger.warning(f"Failed to import customers from {store.name} : {response.text}")

                except Exception as e:
                    _logger.error(f"Error while Importing Customers from {store.name} : {str(e)}")