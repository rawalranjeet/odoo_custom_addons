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


    def _get_specific_processing_values(self, processing_values):
        """ Override of payment to redirect pending token-flow transactions.

        If the financial institution insists on 3-D Secure authentication, this
        override will redirect the user to the provided authorization page.

        Note: `self.ensure_one()`
        """
        res = super()._get_specific_processing_values(processing_values)
        if self._tap_is_authorization_pending():
            res['redirect_form_html'] = self.env['ir.qweb']._render(
                self.provider_id.redirect_form_view_id.id,
                {'api_url': self.tap_3ds_auth_url},
            )
        
        return res

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
        

        if self.payment_method_id.code == 'tap_direct':
            # res['tap_publishable_key'] = self.provider_id.tap_publishable_key
            return res
        
        else: # Redirect flow
            
            base_url = self.provider_id.get_base_url()
            return_url = urls.url_join(base_url, '/payment/tap/return')
            webhook_url = urls.url_join(base_url, '/payment/tap/webhook')
            

            payload = {
                'amount': self.amount,
                'currency': self.currency_id.name,
                'customer_initiated': True,
                'save_card': self.tokenize,
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
        

    # for token payment request
    def _send_payment_request(self):
        """ Override of payment to send a payment request to Tap.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != 'tap':
            return

        # Prepare the payment request to Flutterwave.
        if not self.token_id:
            raise UserError("Tap: " + _("The transaction is not linked to a token."))

        # first create a token
        payload = {
            "saved_card": {
                "card_id": self.token_id.tap_card_id,
                "customer_id": self.token_id.tap_customer_id,
            },
            "client_ip": payment_utils.get_customer_ip_address()
		}

        # Make the token request to Tap.
        response = self.provider_id._tap_make_request('tokens', payload=payload, method='POST')
        token_payment_response_data = self._tap_token_payment(response)

        self._handle_notification_data('tap', token_payment_response_data)


    def _process_notification_data(self, notification_data):
        if self.provider_code != 'tap':
            return super()._process_notification_data(notification_data)
        
        charge_id = notification_data.get('id') or notification_data.get('tap_id')

        verified_data = self.provider_id._tap_make_request(f'charges/{charge_id}', method='GET')

        status = verified_data.get('status')
        
        #update the provider_reference
        self.provider_reference = verified_data.get('id')


        if status == 'CAPTURED':
            self._set_done()
            if self.tokenize and not self.token_id: #save card details for token payment
                self._tap_tokenize_from_notification_data(verified_data)
        elif status in ['DECLINED', 'FAILED', 'CANCELLED', 'ABANDONED', 'TIMEDOUT', 'UNKNOWN']:
            error_message = verified_data.get('response', {}).get('message', _('Payment was unsuccessful.'))
            self._set_canceled(f"Tap: {error_message}")
        else:
            # will be set back to the actual value after moving away from pending
            self.tap_3ds_auth_url = verified_data.get('transaction', {}).get('url')
            self._set_pending()



    # direct payment
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

    
    def _tap_tokenize_from_notification_data(self, notification_data):
        """ Create a new token based on the notification data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        """

        self.ensure_one()

        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_details': notification_data['card']['last_four'],
            'partner_id': self.partner_id.id,
            'provider_ref': self.provider_reference,
            'tap_customer_id': notification_data['customer']['id'],
            'tap_card_id': notification_data['card']['id'],
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                'token_id': token.id,
                'partner_id': self.partner_id.id,
                'ref': self.reference,
            },
        )

    

    def _tap_token_payment(self, notification_data):
        self.ensure_one()
        payload = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'customer_initiated': True,
            'save_card': False,
            'description': self.reference,
            'reference': {'transaction': self.reference, 'order': self.reference},
            'customer': {'first_name': self.partner_name, 'email': self.partner_email, 'id':notification_data['card']['customer']},
            'source': {'id': notification_data['id']},
            'redirect': {'url': self.get_base_url() + '/payment/tap/return'}
        }
        response_data = self.provider_id._tap_make_request('charges', payload=payload, method='POST')

        self.provider_reference = response_data.get('id')

        return response_data


    def _tap_is_authorization_pending(self):
        return self.filtered_domain([
            ('provider_code', '=', 'tap'),
            ('operation', '=', 'online_token'),
            ('state', '=', 'pending'),
            ('tap_3ds_auth_url', 'ilike', 'https'),
        ])