from odoo import fields,api,_,models
from werkzeug.urls import url_join


class PaymentTapCron(models.Model):
    _name = "payment.tap.cron"
    _description="Payment Tap Cron"

    def action_customer_payments(self):
        tap_provider = self.env['payment.provider'].sudo().search([('code','=','tap'),('state','!=','disabled')])
        tap_payment_method = self.env['payment.method'].sudo().search([('code', '=', 'tap_redirect')], limit=1)
        

        if tap_provider and tap_payment_method:
            
            invoices = self.env['account.move'].sudo().search([('move_type','=','out_invoice'),('state','=','posted'),('payment_state','in',['not_paid','partial'])])
            
            for invoice in invoices:
                payment_token = self.env['payment.token'].sudo().search([('provider_id','=',tap_provider.id),('partner_id','=',invoice.partner_id.id)], limit=1)

                if payment_token:
                    tx = self.env['payment.transaction'].sudo().search([
                        ('provider_id','=',tap_provider.id),
                        ('payment_method_id','=',tap_payment_method.id),
                        ('state','in',['draft','pending']),
                        ('invoice_ids','in',[invoice.id]),
                        ('token_id','=',payment_token.id),
                        ('amount','=',invoice.amount_residual),
                        ], limit=1)

                    if not tx:
                        tx = self.env['payment.transaction'].sudo().create({
                            'provider_id': tap_provider.id,
                            'amount': invoice.amount_residual,
                            'currency_id': invoice.currency_id.id,
                            'partner_id': invoice.partner_id.id,
                            'invoice_ids': [(4, invoice.id)],
                            'payment_method_id': tap_payment_method.id,
                            'token_id': payment_token.id,
                        })
                    
                    # start the payment if not already
                    if tx.state == 'draft':
                        tx._send_payment_request()

                    if tx.state == 'done':

                        payment_method_line_id = self.env['account.payment.method.line'].sudo().search([('code', '=', 'tap')])

                        # create a corresponding payment
                        payment = self.env['account.payment'].sudo().create({
                            'partner_id' : tx.partner_id.id,
                            'amount' : tx.amount,
                            'journal_id': tx.provider_id.journal_id.id,
                            'payment_method_line_id' : payment_method_line_id.id,
                            'memo' : tx.provider_reference,
                            'payment_transaction_id' : tx.id,
                            'invoice_ids': [(4, invoice.id)],
                            'payment_token_id': payment_token.id,
                        })

                        payment.action_post()
                        tx.payment_id = payment.id

                        # import pdb; pdb.set_trace()
                            
                        # for line in invoice.line_ids:
                        #     if line.reconciled == False and line.parent_state == 'posted':
                        #         line.reconcile()
                    
                    


# class AccountMove(models.Model):
#     _inherit = "account.move"

#     @api.onchange('ref')
#     def name_change(self):
#         import pdb; pdb.set_trace()


# class AccountPaymentRegister(models.TransientModel):
#     _inherit = "account.payment.register"

#     def _reconcile_payments(self, to_process, edit_mode=False):
#         import pdb; pdb.set_trace()
#         """ Reconcile the payments.

#         :param to_process:  A list of python dictionary, one for each payment to create, containing:
#                             * create_vals:  The values used for the 'create' method.
#                             * to_reconcile: The journal items to perform the reconciliation.
#                             * batch:        A python dict containing everything you want about the source journal items
#                                             to which a payment will be created (see '_compute_batches').
#         :param edit_mode:   Is the wizard in edition mode.
#         """
#         domain = [
#             ('parent_state', '=', 'posted'),
#             ('account_type', 'in', self.env['account.payment']._get_valid_payment_account_types()),
#             ('reconciled', '=', False),
#         ]
#         for vals in to_process:
#             payment = vals['payment']
#             payment_lines = payment.move_id.line_ids.filtered_domain(domain)
#             lines = vals['to_reconcile']
#             extra_context = {'forced_rate_from_register_payment': vals['rate']} if 'rate' in vals else {}

#             for account in payment_lines.account_id:
#                 (payment_lines + lines)\
#                     .with_context(**extra_context)\
#                     .filtered_domain([
#                         ('account_id', '=', account.id),
#                         ('reconciled', '=', False),
#                         ('parent_state', '=', 'posted'),
#                     ])\
#                     .reconcile()
#             lines.move_id.matched_payment_ids += payment