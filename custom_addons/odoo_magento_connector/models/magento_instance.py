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
        
        url = f'{self.magento_store_base_url}/rest/V1{endpoint}'

        headers = {'Authorization': f'Bearer {self.magento_access_token}', 'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, params= params,json = payload, verify=False, headers=headers, timeout=10)
            elif method == 'POST': 
                response = requests.post(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
            elif method == 'PUT':
                response = requests.put(url, params= params, json = payload, verify=False, headers=headers, timeout=20)
        
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
                ]
            }
        }

        return self.magento_make_request(f'/products/{product_template.magento_sku_id}', params, payload, 'PUT')
    
    def magento_update_customer(self, partner, vals):
        params = ''

        full_name = partner.name
        parts = full_name.strip().split()

        first_name = parts[0] if len(parts) > 0 else ""
        middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        if not last_name:
            raise UserError("Please provide last name for the customer")

        payload = {
            "customer": {
                "firstname": first_name,
                "middlename": middle_name,
                "lastname": last_name,
                "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                "dob" : partner.dob.strftime("%Y-%m-%d") if partner.dob else False,
                "email": partner.email,
            }
        }


        return self.magento_make_request(f'/customers/{partner.magento_customer_id}', params, payload, 'PUT')


    def magento_update_customer_address(self, partner, vals):
        params = ''

        if partner.street and partner.country_id and partner.city and partner.zip and partner.phone:
                        
            if partner.state_id:
                region = {
                    "region_code": partner.state_id.code,
                    "region": partner.state_id.name,
                }
            else:
                region = {}

            full_name = partner.name
            parts = full_name.strip().split()

            first_name = parts[0] if len(parts) > 0 else ""
            middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
            last_name = parts[-1] if len(parts) > 1 else ""

            if not last_name or not first_name:
                raise UserError("Please provide first and last name for the customer")
            
            address = {
                    "id": partner.magento_address_id,
                    "customer_id": partner.parent_id.magento_customer_id,
                    "street": [partner.street, partner.street2],
                    "city": partner.city,
                    "postcode": partner.zip,
                    "telephone": partner.phone,
                    "country_id": partner.country_id.code,
                    "region": region,
                    "firstname": first_name,
                    "lastname": last_name,
                    "middlename": middle_name,
                }

            payload = {
                "customer": {
                    "addresses": [address]
                }
            }


            return self.magento_make_request(f'/customers/{partner.parent_id.magento_customer_id}', params, payload, 'PUT')


    # CREATE Methods:::::::::::

    def magento_create_customer(self, partner):
        params = ''

        full_name = partner.name
        parts = full_name.strip().split()

        first_name = parts[0] if len(parts) > 0 else ""
        middle_name = " ".join(parts[1:-1]) if len(parts) > 2 else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        if not last_name:
            raise UserError("Please provide last name for the customer")
        
        if not partner.email:
            raise UserError("Please provide the email for the customer")

        payload = {
            "customer": {
                "firstname": first_name,
                "middlename": middle_name,
                "lastname": last_name,
                "gender": 1 if partner.gender == 'male' else 2 if partner.gender == 'female' else 3,
                "dob" : partner.dob.strftime("%Y-%m-%d") if partner.dob else False,
                "email": partner.email,
            }
        }


        return self.magento_make_request('/customers', params, payload, 'POST')        

