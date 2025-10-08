from odoo import fields, api, _, models
import requests
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger("__name__")


ODOO_TO_MAGENTO_PRODUCT_TYPE = {
    'consu': 'simple',
    'service': 'virtual',
    'combo': 'grouped'
}

MAGENTO_TO_ODOO_PRODUCT_TYPE = {
    'simple': 'consu',
    'configurable' : 'consu',
    'bundle': 'combo',
    'grouped': 'combo',
    'virtual': 'service',
    'downloadable': 'service'
}


class MagentoInstance(models.Model):
    _name = "magento.instance"
    _description = "Magento Instance"


    name = fields.Char()
    magento_access_token = fields.Char()
    magento_store_base_url = fields.Char(required=True)

    magento_username = fields.Char(required=True)
    magento_password = fields.Char(required=True)


    def action_test_connection(self):
        url = f'{self.magento_store_base_url}/rest/V1/store/websites'

        headers={'Authorization': f'Bearer {self.magento_access_token}', 'Content-Type': 'application/json'}

        try:
            response = requests.get(url, params='', verify=False, headers=headers)

            if response.status_code == 200:

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Magento Connection Success'),
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
                        'title': _('Magento Connection Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }
        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
        

    def action_generate_access_token(self):
        url = f'{self.magento_store_base_url}/rest/V1/integration/admin/token'

        headers={'Content-Type': 'application/json'}

        payload = {
            "username": self.magento_username,
            "password": self.magento_password
            }

        try:
            response = requests.post(url, params='', verify=False, headers=headers, json=payload)


            if response.status_code == 200:
                self.magento_access_token = response.json()

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Magento Connection Success'),
                        'message': _('New Token Generated'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Magento Connection Failed'),
                        'message': response.text,
                        'type': 'danger',
                        'sticky': False,
                    },
                }
        except Exception as e:
            raise UserError(_(f"Connection error: {str(e)}"))
        

    def magento_make_request(self, endpoint, params, payload=None, method='GET'):

        self.action_generate_access_token()
        
        url = f'{self.magento_store_base_url}/rest/V1{endpoint}'

        headers = {
            'Authorization': f'Bearer {self.magento_access_token}',
            'Content-Type': 'application/json',
            'X-Odoo-Operation': 'true'
        }

        try:
            if method == 'GET':
                response = requests.get(url, params= params,json = payload, verify=False, headers=headers, timeout=10)
            elif method == 'POST': 
                response = requests.post(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
            elif method == 'PUT':
                response = requests.put(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
            elif method == 'DELETE':
                response = requests.delete(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
        
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            _logger.exception(e.response.json())
            raise UserError(f"Magento API Error: {e.response.json().get('message')}")
        
        except requests.exceptions.RequestException as e:
        # Any network/connection/timeout/DNS errors
            _logger.exception(e)
            raise UserError(f"Magento Connection Error: It may be due to store url you provided is either invalid or the server is down")

        except Exception as e:
            _logger.exception(e)
            # raise UserError(f"Magento API Error: {(e.response.json().get('message', 'Unknown Magento API error')).replace('%1', e.response.json().get('parameters', [''])[0])}")
            raise UserError(f"An error occurred: {e}")
        
    


    # UPDATE methods :::::::::::
    def magento_update_product(self, product_template, vals):
        
        params = ''

        url_key = f"{"-".join(product_template.name.lower().split()).replace("'", "")}-{product_template.id}"

        payload = {
            "product": {
                "name": product_template.name,
                "price": product_template.list_price,
                "status": 1 if product_template.is_published else 2,
                "type_id": ODOO_TO_MAGENTO_PRODUCT_TYPE[product_template.type],
                "custom_attributes": [
                    { "attribute_code": "description", "value": product_template.description },
                    { "attribute_code": "url_key", "value": url_key },
                ],
                "extension_attributes": {
                    "stock_item": {
                        "qty": product_template.qty_available,
                        "is_in_stock": True if product_template.qty_available > 0 else False,
                    },
                    "category_links": [
                        {
                            "position": 0,
                            "category_id": "2"
                        }
                    ],
                }
            }
        }

        return self.magento_make_request(f'/products/{product_template.magento_sku_id}', params, payload, 'PUT')
    
    
    def magento_update_customer(self, partner, vals):
        params = ''

        first_name, middle_name, last_name = self.get_magento_name(partner.name)

        if not last_name:
            raise UserError("Please provide last name for the customer")
        

        addresses = []

        for child_partner in partner.child_ids:

            child_first_name, child_middle_name, child_last_name = self.get_magento_name(child_partner.name)

            if not child_first_name or not child_last_name or not child_partner.phone or not child_partner.street or not child_partner.city or not child_partner.zip or not child_partner.country_id:
                continue;

            address = {
                    "firstname": child_first_name,
                    "middlename": child_middle_name,
                    "lastname": child_last_name,
                    "street": [child_partner.street, child_partner.street2],
                    "city": child_partner.city,
                    "postcode": child_partner.zip,
                    "telephone": child_partner.phone,
                    "country_id": child_partner.country_code,
                    "region": {
                        "region_code": child_partner.state_id.code,
                        "region": child_partner.state_id.name,
                    } if child_partner.state_id else {},
                    "default_shipping": True if child_partner.type == 'delivery' else False,
                    "default_billing": True if child_partner.type == 'invoice' else False,
                }

            if child_partner.magento_address_id:
                address['id'] = child_partner.magento_address_id
            
            addresses.append(address)

        payload = {
            "customer": {
                "firstname": first_name,
                "middlename": middle_name,
                "lastname": last_name,
                "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                "dob" : partner.dob.strftime("%Y-%m-%d") if partner.dob else False,
                "email": partner.email,
                "addresses": addresses,
            }
        }


        return self.magento_make_request(f'/customers/{partner.magento_customer_id}', params, payload, 'PUT')

    def magento_update_order(self, order):
        params = ''

        payload = {
           
        }

        return True;


    # CREATE Methods :::::::::::

    def magento_create_customer(self, partner):
        params = ''

        first_name, middle_name, last_name = self.get_magento_name(partner.name)

        if not last_name:
            raise UserError("Please provide last name for the customer")
        
        if not partner.email and not partner.magento_address_id:
            raise UserError("Please provide the email for the customer")
        
        addresses = []

        for child_partner in partner.child_ids:

            child_first_name, child_middle_name, child_last_name = self.get_magento_name(child_partner.name)

            if not child_first_name or not child_last_name or not child_partner.phone or not child_partner.street or not child_partner.city or not child_partner.zip or not child_partner.country_id:
                continue;

            address = {
                    "firstname": child_first_name,
                    "middlename": child_middle_name,
                    "lastname": child_last_name,
                    "street": [child_partner.street, child_partner.street2],
                    "city": child_partner.city,
                    "postcode": child_partner.zip,
                    "telephone": child_partner.phone,
                    "country_id": child_partner.country_code,
                    "region": {
                        "region_code": child_partner.state_id.code,
                        "region": child_partner.state_id.name,
                    } if child_partner.state_id else {},
                    "default_shipping": True if child_partner.type == 'delivery' else False,
                    "default_billing": True if child_partner.type == 'invoice' else False,
                }

            if child_partner.magento_address_id:
                address['id'] = child_partner.magento_address_id
            
            addresses.append(address)

        payload = {
            "customer": {
                "firstname": first_name,
                "middlename": middle_name,
                "lastname": last_name,
                "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                "dob" : partner.dob.strftime("%Y-%m-%d") if partner.dob else False,
                "email": partner.email,
                "addresses": addresses,
            }
        }


        return self.magento_make_request('/customers', params, payload, 'POST')
    

    def magento_create_product(self, product_template):
        if not product_template.default_code:
            raise UserError("Please provide default code or SKU for the product")
        
        payload = {
            "product": {
                "sku": product_template.default_code,
                "name": product_template.name,
                "price": product_template.list_price,
                "status": 1 if product_template.is_published else 2,
                "type_id": ODOO_TO_MAGENTO_PRODUCT_TYPE[product_template.type],
                "attribute_set_id": 4,
                "weight": product_template.weight if product_template.weight else 1,
                "visibility": 4,
                "custom_attributes": [
                    { "attribute_code": "description", "value": product_template.description },
                    { "attribute_code": "url_key", "value": f"{"-".join(product_template.name.lower().split()).replace("'", "")}-{product_template.id}" },
                ],
                "extension_attributes": {
                    "stock_item": {
                        "qty": product_template.qty_available,
                        "is_in_stock": True if product_template.qty_available > 0 else False,
                    },
                    "category_links": [
                        {
                            "position": 0,
                            "category_id": "2"
                        }
                    ],
                }
            }
        }

        return self.magento_make_request('/products', '', payload, 'POST')
        
    def magento_create_order(self, order):

        # checking for required fields for creating order in magento
        partner = order.partner_id

        if partner.magento_customer_id is False:
            raise UserError("Please sync the customer to magento before syncing the order")
        
        elif partner.magento_instance_id != self:
            raise UserError("The customer is not linked to the same magento instance as the order")
        
        elif partner.child_ids.filtered(lambda c: c.type == 'delivery' and not c.magento_address_id):
            raise UserError("Please sync the delivery address of the customer to magento before syncing the order")
        
        elif partner.child_ids.filtered(lambda c: c.type == 'invoice' and not c.magento_address_id):
            raise UserError("Please sync the invoice address of the customer to magento before syncing the order")
        
        elif not order.order_line:
            raise UserError("Please add order lines before syncing the order to magento")
        
        
        shipping_address = partner.search([('type', '=', 'delivery'),('parent_id', '=', partner.id)], limit=1)
        billing_address = partner.search([('type', '=', 'invoice'),('parent_id', '=', partner.id)], limit=1)

        if not shipping_address and not billing_address:
            raise UserError("Please set the delivery or invoice address for the customer before syncing the order to magento")
        elif not shipping_address and billing_address:
            shipping_address = billing_address
        elif shipping_address and not billing_address:
            billing_address = shipping_address

        if not shipping_address.state_id or not billing_address.state_id:
            raise UserError("Please select a state for the Invoice and Delivery Address")


        # STEP 1:  create a cart
        cart_response = self.magento_make_request(f'/customers/{partner.magento_customer_id}/carts', '', None, 'POST')
        magento_cart_id = cart_response

        #STEP 2: Add items to cart
        for item in order.order_line:

            # Ensure product is synced to Magento
            if not item.product_template_id.magento_sku_id:
                raise UserError(f"Please sync the product '{item.product_template_id.name}' to Magento before syncing the order")

            if item.magento_is_added_line:
                continue
            else:
                item.magento_is_added_line = True

            account_tax = item.tax_id

            if account_tax:
                

                # search for exisiting tax rate
                params = {
                        "searchCriteria[filter_groups][0][filters][0][field]":"rate",
                        "searchCriteria[filter_groups][0][filters][0][value]": account_tax.amount,
                        "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",

                        "searchCriteria[filter_groups][1][filters][0][field]": "tax_country_id",
                        "searchCriteria[filter_groups][1][filters][0][value]": shipping_address.country_id.code,
                        "searchCriteria[filter_groups][1][filters][0][condition_type]": "eq",
                    }

                tax_response = self.magento_make_request('/taxRates/search', params, None, 'GET')

                if not tax_response.get('items'):
                    tax_rate_payload = {
                        "taxRate": {
                            "code": f"{shipping_address.country_id.code}-{account_tax.amount}",
                            "rate": account_tax.amount,
                            "tax_country_id": shipping_address.country_id.code,
                            "tax_postcode": "*"
                        }
                    }

                    new_tax_rate = self.magento_make_request('/taxRates', '', tax_rate_payload, 'POST')

                    # adding it to the tax rule (TAXABLE GOODS)
                    tax_rule = self.magento_make_request('/taxRules/1', '', None, 'GET')


                    tax_rule_payload = {
                        "rule":{
                            **tax_rule,
                            "tax_rate_ids": [*tax_rule.get('tax_rate_ids', []), new_tax_rate.get('id')]
                        }
                    }
                    
                    self.magento_make_request('/taxRules', '', tax_rule_payload, 'PUT')


            item_payload = {
                "cartItem": {
                    "sku": item.product_template_id.magento_sku_id,
                    "qty": item.product_uom_qty,
                    "quote_id": magento_cart_id,
                    # "extension_attributes":{
                    #     "discounts": [
                    #         {
                    #             "discount_data":{
                    #                 "amount": 0,
                    #                 "base_amount": 0,
                    #                 "base_original_amount": 0,
                    #                 "original_amount": 0,
                    #                 "rule_i_d": 1,
                    #                 "rule_label": "Rule1"
                    #             }
                    #         }
                    #     ]
                    # }
                }
            }

            self.magento_make_request(f'/carts/{magento_cart_id}/items', '', item_payload, 'POST')

        
        # STEP 3: Set shipping and billing address

        shipping_first_name, shipping_middle_name, shipping_last_name = self.get_magento_name(shipping_address.name)
        billing_first_name, billing_middle_name, billing_last_name = self.get_magento_name(billing_address.name)

        address_payload = {
            "addressInformation": {
                "shipping_address": {
                    "firstname": shipping_first_name,
                    "middlename": shipping_middle_name,
                    "lastname": shipping_last_name,
                    "street": [shipping_address.street, shipping_address.street2],
                    "city": shipping_address.city,
                    "region": shipping_address.state_id.code,
                    "postcode": shipping_address.zip,
                    "country_id": shipping_address.country_code,
                    "telephone": shipping_address.phone,
                    "email": partner.email,
                },
                "billing_address": {
                    "firstname": billing_first_name,
                    "middlename": billing_middle_name,
                    "lastname": billing_last_name,
                    "street": [billing_address.street, billing_address.street2],
                    "city": billing_address.city,
                    "region": billing_address.state_id.code,
                    "postcode": billing_address.zip,
                    "country_id": billing_address.country_code,
                    "telephone": billing_address.phone,
                    "email": partner.email,
                },

                "shipping_method_code": "flatrate",
                "shipping_carrier_code": "flatrate"
            }
        }

        self.magento_make_request(f'/carts/{magento_cart_id}/shipping-information', '', address_payload, 'POST')

        
        # STEP 4: payment methods
        payment_payload = {
            "method": {
                "method": "checkmo"   # Payment method code
            }
        }

        self.magento_make_request(f'/carts/{magento_cart_id}/selected-payment-method', '', payment_payload, 'PUT')

        # STEP 5: create an order
        magento_order_id = self.magento_make_request(f'/carts/{magento_cart_id}/order', '', None, 'PUT')

        return {
            "magento_order_id" : magento_order_id,
            "magento_cart_id": magento_cart_id
        }




    # DELETE Methods :::::::::::
    def magento_delete_customer(self, partner):
        return self.magento_make_request(f'/customers/{partner.magento_customer_id}', '', None, 'DELETE')
    
    def magento_delete_products(self, magento_sku_ids):
        for sku in magento_sku_ids:
            result = self.magento_make_request(f'/products/{sku}', '', None, 'DELETE')

            if result is False:
                return False
            
        return True

    def magento_cancel_order(self, magento_order_id):
        return self.magento_make_request(f'/orders/{magento_order_id}/cancel', '', None, 'POST')
    

    # Helper Methods :::::::::::
    def get_magento_name(self, name):

        parts = name.strip().split()

        first_name = parts[0] if len(parts) > 0 else ""
        middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        return first_name, middle_name, last_name     



    
