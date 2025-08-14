# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TapController(http.Controller):

    @http.route('/payment/tap/create_charge', type='json', auth='public')
    def tap_create_charge(self, reference, token_id):
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
        _logger.info("Handling Tap return with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction']._handle_notification_data('tap', data)
        return request.redirect('/payment/status')





    # @http.route('/payment/tap/webhook', type='json', auth='public', csrf=False)
    # def tap_webhook(self, **kwargs):
    #     data = request.jsonrequest
    #     _logger.info("Handling Tap webhook with data:\n%s", pprint.pformat(data))
    #     try:
    #         request.env['payment.transaction']._handle_notification_data('tap', data)
    #     except Exception as e:
    #         _logger.exception("Failed to handle Tap webhook notification: %s", e)
    #     return http.Response(status=200)