# -*- coding: utf-8 -*-
import logging
from werkzeug import urls
from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransactionTap(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        if provider_code != 'tap':
            return super()._get_tx_from_notification_data(provider_code, notification_data)
        provider_ref = notification_data.get('id') or notification_data.get('tap_id')
        if not provider_ref:
            raise ValidationError("Tap: " + _("Received notification data with missing charge ID."))
        tx = self.search([('provider_reference', '=', provider_ref), ('provider_code', '=', 'tap')])
        if not tx:
            raise ValidationError("Tap: " + _("No transaction found matching provider reference %s.", provider_ref))
        return tx

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'tap':
            return res

        if self.provider_id.tap_payment_flow_type == 'direct':
            res['tap_publishable_key'] = self.provider_id.tap_publishable_key
            return res
        
        else: # Redirect flow
            
            base_url = self.provider_id.get_base_url()
            return_url = urls.url_join(base_url, '/payment/tap/return')
            webhook_url = urls.url_join(base_url, '/payment/tap/webhook')
            
            payload = {
                'amount': self.amount,
                'currency': self.currency_id.name,
                'customer_initiated': True,
                'save_card': False,
                'description': self.reference,
                'reference': {'transaction': self.reference, 'order': self.reference},
                'customer': {'first_name': self.partner_name, 'email': self.partner_email},
                'source': {'id': 'src_all'},
                'redirect': {'url': return_url},
                'post': {'url': webhook_url}
            }

            response_data = self.provider_id._tap_make_request('charges', payload=payload, method='POST')
            redirect_url = response_data.get('transaction', {}).get('url')

            if not redirect_url:
                raise ValidationError(_("Tap payment service returned an invalid response."))
            
            self.provider_reference = response_data.get('id')

            parsed_url = urls.url_parse(redirect_url)
            params = dict(parsed_url.decode_query())
            base_redirect_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

            return {'api_url': base_redirect_url, 'url_params': params}
        

    def _tap_create_charge_from_token(self, token_id):
        self.ensure_one()
        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'customer_initiated': True,
            'save_card': False,
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

    def _process_notification_data(self, notification_data):
        if self.provider_code != 'tap':
            return super()._process_notification_data(notification_data)
        
        charge_id = notification_data.get('id') or notification_data.get('tap_id')

        verified_data = self.provider_id._tap_make_request(f'charges/{charge_id}', method='GET')

        status = verified_data.get('status')

        if status == 'CAPTURED':
            self._set_done()
        elif status in ['DECLINED', 'FAILED', 'CANCELLED', 'ABANDONED', 'TIMEDOUT', 'UNKNOWN']:
            error_message = verified_data.get('response', {}).get('message', _('Payment was unsuccessful.'))
            self._set_canceled(f"Tap: {error_message}")
        else:
            self._set_pending()