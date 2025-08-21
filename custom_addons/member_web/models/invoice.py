from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    membership_id = fields.Many2one("membership.membership", string="Membership")
    membership_date = fields.Date(string="Membership Date")
    expiry_date = fields.Date(string="Expiry Date")

    member_id = fields.Many2one("membership.membership", string="Membership")

    @api.model
    def create(self, vals):
        move = super().create(vals)

        membership = move.membership_id
        if membership:
            move.membership_date = membership.membership_date
            move.expiry_date = membership.expiry_date

        return move

    def action_post(self):
        res = super().action_post()

        for move in self:
            membership = move.membership_id
            if (
                membership
                and move.is_renewal_invoice
                and move.move_type == "out_invoice"
                and move.state == "posted"
                and membership.duration_id
                and membership.expiry_date
            ):
                old_expiry = membership.expiry_date
                duration_months = int(membership.duration_id.duration_value)

                membership.membership_date = old_expiry
                membership.expiry_date = old_expiry + relativedelta(
                    months=+duration_months
                )

                move.membership_date = membership.membership_date
                move.expiry_date = membership.expiry_date

        return res
