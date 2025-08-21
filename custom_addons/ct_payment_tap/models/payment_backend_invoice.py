from odoo import _, fields, models,api
from werkzeug.urls import url_join


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):

        if self.payment_method_code == 'tap':

            tap_provider = self.env['payment.provider'].search([('code', '=', 'tap')], limit=1)
            tap_payment_method = self.env['payment.method'].search([('code', '=', 'tap_redirect')], limit=1)

            # Create a payment transaction instead of a standard payment
            invoice = self.env['account.move'].browse(self._context.get('active_id'))

            tx = self.env['payment.transaction'].create({
                'provider_id': tap_provider.id,
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'invoice_ids': [(4, invoice.id)],
                'payment_method_id': tap_payment_method.id,
            })

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            # Construct the full, absolute return URL
            return_url = url_join(base_url, f"/payment/tap/return?invoice_id={invoice.id}")

            payload = {
                'amount': self.amount,
                'currency': self.currency_id.name,
                'customer_initiated': True,
                'save_card': False,
                'description': tx.reference,
                'reference': {'transaction': tx.reference, 'order': tx.reference},
                'customer': {'first_name': self.partner_id.name, 'email': self.partner_id.email},
                'source': {'id': 'src_all'},
                'redirect': {'url': return_url},
                'post': {'url': ''}
            }

            response_data = tap_provider._tap_make_request('charges', payload=payload, method='POST')
            redirect_url = response_data.get('transaction', {}).get('url')

            tx.provider_reference = response_data.get('id')

            # Return an action to open the payment link in current tab
            return {
                'type': 'ir.actions.act_url',
                'url': redirect_url,
                'target': 'self',
            }
            
        else:
            return super().action_create_payments()
