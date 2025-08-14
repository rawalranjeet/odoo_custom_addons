from odoo import models, fields, api

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    use_payment_terminal = fields.Selection(
        selection=lambda self: self._get_payment_terminal_selection(),
        string='Use EFT Pay Terminal',
        help='Record payments with a specific EFT Pay terminal.'
    )

    eft_user_confirm_key = fields.Char(string="Merchant Confirm Key", help="Your User Confirm Key from EFT Pay.")
    eft_secret_key = fields.Char(string="Merchant Secret Key", password=True, help="Your Secret Key from EFT Pay.")

    @api.model
    def _get_payment_terminal_selection(self):
        """Dynamically return available terminals based on config settings."""
        params = self.env['ir.config_parameter'].sudo()
        options = [('none', 'Not an EFT Pay method')] # Default option

        if params.get_param('pos_eftpay.pos_alipay_enabled'):
            options.append(('alipay', 'Alipay'))
        if params.get_param('pos_eftpay.pos_wechat_enabled'):
            options.append(('wechat', 'WeChat Pay'))
        if params.get_param('pos_eftpay.pos_fps_enabled'):
            options.append(('fps', 'FPS'))
        if params.get_param('pos_eftpay.pos_payme_enabled'):
            options.append(('payme', 'PayMe'))
        if params.get_param('pos_eftpay.pos_unionpay_enabled'):
            options.append(('unionpay', 'UnionPay'))

        return options