from odoo import fields, api, _, models
import requests
from odoo.exceptions import UserError


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
        
