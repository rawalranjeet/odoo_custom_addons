from odoo import api, fields, models


class PaymentToken(models.Model):
    _inherit = "payment.token"


    tap_customer_id = fields.Char()
    tap_card_id = fields.Char()

    