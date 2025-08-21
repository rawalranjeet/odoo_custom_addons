from odoo import models, fields, api


class MembershipDuration(models.Model):
    _name = "membership.duration"
    _description = "Membership Duration"

    name = fields.Char(string="Name", required=True)
    duration_value = fields.Integer(string="Duration", required=True)
    product_id = fields.Many2one("product.product", string="Product")

    def name_get(self):
        result = []
        for record in self:
            display_name = f"{record.duration_value}"
            result.append((record.id, display_name))
        return result

    @api.onchange("duration_value")
    def _onchange_duration_value(self):
        """Convert entered days into months automatically."""
        for record in self:
            if record.duration_value:
                record.duration_value = round(record.duration_value / 30.44)
