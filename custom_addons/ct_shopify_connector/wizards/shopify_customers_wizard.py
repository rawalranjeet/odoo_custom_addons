from odoo import _,api, models, fields
from odoo.exceptions import UserError
import requests


class ShopifyCustomersWizard(models.TransientModel):
    _name = "shopify.customers.wizard"

    shopify_store_id = fields.Many2one("shopify.store", required=True)

    def action_get_customers(self):
        url = f'https://{self.shopify_store_id.shopify_store_name}.myshopify.com/admin/api/2025-07/customers.json'
        
        headers = {
            'Content-Type':'application/json',
            'X-Shopify-Access-Token': self.shopify_store_id.shopify_access_token
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
                            'shopify_store_id': self.shopify_store_id.id,
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
                                'shopify_store_id': self.shopify_store_id.id,
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
                        

                        # log

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Shopify Customer Success'),
                        'message': _(f'Customer Fetched, {total_customer_fetched} in total'),
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
