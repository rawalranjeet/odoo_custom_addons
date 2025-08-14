# -*- coding: utf-8 -*-
import logging
from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransactionTap(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Override of payment to find the transaction based on Tap's data.
        """
        if provider_code != 'tap':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        provider_ref = notification_data.get('id') or notification_data.get('tap_id')
        if not provider_ref:
            raise ValidationError("Tap: " + _("Received notification data with missing charge ID."))
        
        tx = self.search([('provider_reference', '=', provider_ref), ('provider_code', '=', 'tap')])
        if not tx:
            raise ValidationError("Tap: " + _("No transaction found matching provider reference %s.", provider_ref))
        return tx

    def _get_specific_processing_values(self, processing_values):
        """
        Override of payment to return Tap-specific rendering values for the inline form.
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'tap':
            return res

        res['tap_publishable_key'] = self.provider_id.tap_publishable_key
        return res

    def _tap_create_charge_from_token(self, token_id):
        """
        Create a charge on Tap's side using a token and handle 3D Secure.
        """
        self.ensure_one()
        
        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'customer_initiated': True,
            'save_card': False,
            'description': self.reference,
            'statement_descriptor': self.reference,
            'reference': {'transaction': self.reference, 'order': self.reference},
            'customer': {'first_name': self.partner_name, 'email': self.partner_email},
            'source': {'id': token_id},
            'redirect': {'url': self.get_base_url() + '/payment/tap/return'} # Use custom return URL
        }

        response_data = self.provider_id._tap_make_request('charges', payload=payload, method='POST')
        
        self.provider_reference = response_data.get('id')
        self._process_notification_data(response_data)

        if response_data.get('status') == 'INITIATED' and response_data.get('transaction', {}).get('url'):
            return {'three_ds_redirect_url': response_data['transaction']['url']}
        return {}


    def _process_notification_data(self, notification_data):
        """
        Override of payment to process the notification data from Tap.
        """
        if self.provider_code != 'tap':
            return super()._process_notification_data(notification_data)

        # Re-fetch the charge from Tap to get the final status
        charge_id = notification_data.get('id') or notification_data.get('tap_id')
        verified_data = self.provider_id._tap_make_request(f'charges/{charge_id}', method='GET')
        
        status = verified_data.get('status')
        if status == 'CAPTURED':
            self._set_done()
        elif status in ['DECLINED', 'FAILED', 'CANCELLED', 'ABANDONED', 'TIMEDOUT', 'UNKNOWN']:
            error_message = verified_data.get('response', {}).get('message', _('Payment was unsuccessful.'))
            self._set_canceled(f"Tap: {error_message}")
        else: # INITIATED or any other status
            self._set_pending()
