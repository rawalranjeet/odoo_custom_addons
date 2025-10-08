# -*- coding: utf-8 -*-
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.ct_payment_tap.controllers.main import TapController as TestController

class TapController(TestController):

    @http.route('/payment/tap/return', type='http', auth='public', csrf=False, save_session=False)
    def tap_return_from_checkout(self, **data):
        _logger.info("Handling Tap return with data:\n%s", pprint.pformat(data))
        tx = request.env['payment.transaction']._handle_notification_data('tap', data)


        # for payment from backend
        invoice_id = data.get('invoice_id')
        if invoice_id:
            invoice = request.env['account.move'].sudo().browse(int(invoice_id))
            if invoice.exists():
                return request.redirect(f'/odoo/customer-invoices/{invoice_id}')
            
        return request.redirect('/payment/status')
    
