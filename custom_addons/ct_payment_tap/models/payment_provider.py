# -*- coding: utf-8 -*-
import logging
import requests
import pprint
import json
from werkzeug import urls

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentProviderTap(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('tap', 'Tap')],
        ondelete={'tap': 'set default'}
    )
    tap_secret_key = fields.Char(
        string='Secret Key',
    )
    tap_publishable_key = fields.Char(
        string='Publishable Key',
        help="Only used for the Direct flow type.",
    )

    tap_3ds_verification = fields.Boolean(
        string = "Require 3DS Verfication?",
        default = True
    )

    tap_payment_flow_type = fields.Selection(
        [
            ('redirect', 'Redirect'),
            ('direct', 'Direct')
        ],
        string='Payment Flow Type',
        default='redirect',
        required=True,
        help="Choose how the customer will complete their payment."
    )

    def _get_tap_api_url(self):
        """Returns the base URL for the Tap API."""
        return 'https://api.tap.company/v2/'

    def _tap_make_request(self, endpoint, payload=None, method='POST'):
        """
        Make a request to Tap API at the specified endpoint.
        """
        self.ensure_one()
        url = urls.url_join(self._get_tap_api_url(), endpoint)
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            'Authorization': f'Bearer {self.tap_secret_key}',
        }

        try:
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=10)
            else: # POST
                
                payload['threeDSecure'] = self.tap_3ds_verification
                response = requests.post(url, json=payload, headers=headers, timeout=20)
            
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # import pdb; pdb.set_trace()
            _logger.exception("Invalid API request at %s with data:\n%s", url, pprint.pformat(payload))
            raise ValidationError("Tap: " + _(e.response.json().get('errors')[0].get('description')))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError("Tap: " + _("Could not establish the connection to the API."))

        
        return response.json()

    def _tap_get_inline_form_values(self, **kwargs):
        """
        Return a serialized JSON of the required values to render the inline form.
        """
        self.ensure_one()
        return json.dumps({
            'publishable_key': self.tap_publishable_key,
            'tap_payment_flow_type': self.tap_payment_flow_type
        })