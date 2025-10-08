from odoo import _, api, models, fields

class PaymentTransactionTap(models.Model):
    _inherit = 'payment.transaction'
    
    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)

        if self.provider_code != 'tap':
            return
        
        if self.state in ['pending', 'authorized'] and self.payment_id:
            self.payment_id.post()

        elif self.state == 'done' and self.payment_id:
            self.payment_id.action_post()
            self.payment_id.action_validate()

        elif self.state in ['cancel', 'error'] and self.payment_id:
            self.payment_id.action_cancel()

