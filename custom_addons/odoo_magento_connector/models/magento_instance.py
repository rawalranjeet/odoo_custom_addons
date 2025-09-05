from odoo import fields, api, _, models
import requests
from odoo.exceptions import UserError


class MagentoInstance(models.Model):
    _name = "magento.instance"
    _description = "Magento Instance"


    name = fields.Char()
    magento_access_token = fields.Char(required=True)
    magento_store_base_url = fields.Char(required=True)


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
