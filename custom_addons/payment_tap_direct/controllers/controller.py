# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TapController(http.Controller):

    @http.route('/payment/tap/create_charge', type='json', auth='public')
    def tap_create_charge(self, reference, token_id):
        """
        This route is called by the JS when it has a token.
        It creates the charge on the backend and returns the status.
        """
        try:
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
            if not tx:
                return {'error': 'Transaction not found'}

            result = tx._tap_create_charge_from_token(token_id)
            
            return {
                'success': True,
                'three_ds_redirect_url': result.get('three_ds_redirect_url')
            }
        except Exception as e:
            _logger.exception("Failed to create Tap charge: %s", e)
            return {'error': str(e)}

    @http.route('/payment/tap/return', type='http', auth='public', csrf=False, save_session=False)
    def tap_return_from_checkout(self, **data):
        
        """Handle the return from Tap after a 3DS verification."""
        _logger.info("Handling Tap return with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction']._handle_notification_data('tap', data)
        return request.redirect('/payment/status')
