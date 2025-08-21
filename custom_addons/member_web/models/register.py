from odoo import models, fields, api


class WebsiteMember(models.Model):
    _name = "website.member"
    _description = "Website Member"

    name = fields.Char(string="Name", required=True)
    email = fields.Char(required=True)
    height = fields.Float(string="Height")
    weight = fields.Float(string="Weight")
    dob = fields.Date(string="Date of Birth")
    medical_info = fields.Text(string="Medical Info")
    member_document = fields.Binary(string="Document")
    member_document_filename = fields.Char(string="Filename")
    partner_id = fields.Many2one("res.partner", string="Related Partner")
    membership_ids = fields.One2many(
        "membership.membership", "member_id", string="Memberships"
    )
    user_id = fields.Many2one("res.users", string="Related User")
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_invoice_count"
    )
    invoice_ids = fields.One2many(
        related="partner_id.invoice_ids",
        string="Invoices",
        readonly=True,
    )

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = self.env["account.move"].search_count(
                [
                    ("move_type", "=", "out_invoice"),
                    ("partner_id", "=", record.partner_id.id),
                ]
            )

    def action_view_member_invoices(self):
        self.ensure_one()
        return {
            "name": "Invoices",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("move_type", "=", "out_invoice"),
                ("partner_id", "=", self.partner_id.id),
            ],
            "context": {"default_partner_id": self.partner_id.id},
        }

    @api.model
    def create(self, vals):
        if not vals.get("user_id") and vals.get("email"):
            user = self.env["res.users"].create(
                {
                    "name": vals.get("name"),
                    "login": vals.get("email"),
                }
            )
            vals["user_id"] = user.id
        return super().create(vals)
