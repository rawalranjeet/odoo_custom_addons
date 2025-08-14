from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('hyperpay', "HyperPay")], ondelete={'hyperpay': 'set default'}
    )
    hyperpay_merchant_id = fields.Char(
        string="Merchant Id",
        help="Merchant ID.",
        required_if_provider='hyperpay',
    )
    hyperpay_authorization = fields.Char(
        string="Authorization",
        required_if_provider='hyperpay',
    )