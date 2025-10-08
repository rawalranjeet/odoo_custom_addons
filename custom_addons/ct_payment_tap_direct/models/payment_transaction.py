# -*- coding: utf-8 -*-
import logging
import pprint
from werkzeug import urls
from odoo import _, api, models, fields
from odoo.exceptions import ValidationError, UserError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransactionTap(models.Model):
    _inherit = 'payment.transaction'

    tap_3ds_auth_url = fields.Char()


    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'tap' and self.payment_method_id.code == 'tap_direct':
            return res
        
        
    def _tap_create_charge_from_token(self, token_id):
        self.ensure_one()
        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'customer_initiated': True,
            'save_card': self.tokenize,
            'description': self.reference,
            'reference': {'transaction': self.reference, 'order': self.reference},
            'customer': {'first_name': self.partner_name, 'email': self.partner_email},
            'source': {'id': token_id},
            'redirect': {'url': self.get_base_url() + '/payment/tap/return'}
        }
        response_data = self.provider_id._tap_make_request('charges', payload=payload, method='POST')

        self.provider_reference = response_data.get('id')

        self._process_notification_data(response_data)

        if response_data.get('status') == 'INITIATED' and response_data.get('transaction', {}).get('url'):
            return {'three_ds_redirect_url': response_data['transaction']['url']}
        return {}
    