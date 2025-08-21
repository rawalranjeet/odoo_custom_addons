from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class Membership(models.Model):
    _name = "membership.membership"
    _description = "Membership"

    name = fields.Char(string="Membership Reference", required=True, default="New")
    member_id = fields.Many2one("website.member", string="Member", required=True)
    email = fields.Char(
        related="member_id.email", string="Email", store=True, readonly=False
    )

    @property
    def portal_user(self):
        return self.member_id.user_id

    membership_fees = fields.Float(
        string="Membership Fees",
        compute="_compute_membership_fees",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_membership_fees(self):
        for record in self:
            record.membership_fees = (
                record.product_id.list_price if record.product_id else 0.0
            )

    user_id = fields.Many2one("res.users", string="Related User")
    description = fields.Text(string="Description")
    renewal_invoice_id = fields.Many2one("account.move", string="Renewal Invoice")
    request_date = fields.Date(string="Request Date")
    expiry_date = fields.Date(
        string="Expiry Date", compute="_compute_expiry_date", store=True
    )
    membership_date = fields.Date(string="Membership Date")
    new_membership_date = fields.Date(string="New Membership Date")
    new_expiry_date = fields.Date(string="New Expiry Date")
    responsible_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    invoice_ids = fields.One2many("account.move", "membership_id", string="Invoices")
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_invoice_count"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request", "Requested"),
            ("confirm", "Confirmed"),
            ("active", "Active"),
            ("expired", "Expired"),
        ],
        default="draft",
        string="Status",
    )
    duration_id = fields.Many2one("membership.duration", string="Duration")
    product_id = fields.Many2one(
        "product.product",
        string="Membership Product",
        compute="_compute_product_id",
        store=True,
        readonly=False,
    )

    @api.depends("membership_date", "duration_id.duration_value")
    def _compute_expiry_date(self):
        for record in self:
            if record.membership_date and record.duration_id.duration_value:
                record.expiry_date = record.membership_date + relativedelta(
                    months=int(record.duration_id.duration_value)
                )
            else:
                record.expiry_date = False

    @api.model
    def _send_expiry_reminders(self):
        _logger.info("> Preparing renewal invoices for memberships expiring in 7 days")

        today = fields.Date.today()
        target_date = today + timedelta(days=7)

        memberships = self.search(
            [("expiry_date", "=", target_date), ("state", "=", "active")]
        )

        for membership in memberships:
            paid_invoice = membership.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.payment_state == "paid"
            )
            if not paid_invoice:
                _logger.info(
                    "> Membership %s not renewed, old invoice unpaid", membership.id
                )
                continue

            # Create new renewal invoice
            new_membership_date = membership.expiry_date + timedelta(days=1)
            new_expiry_date = new_membership_date + relativedelta(
                months=int(membership.duration_id.duration_value)
            )

            renewal_invoice = self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": membership.member_id.partner_id.id,
                    "membership_date": new_membership_date,
                    "expiry_date": new_expiry_date,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": membership.product_id.id,
                                "quantity": 1,
                                "price_unit": membership.membership_fees,
                            },
                        )
                    ],
                    "membership_id": membership.id,
                    "is_renewal_invoice": True,
                }
            )
            renewal_invoice.action_post()

            membership.renewal_invoice_id = renewal_invoice.id
            _logger.info(
                "> Renewal invoice %s created for membership %s",
                renewal_invoice.id,
                membership.id,
            )

            if not renewal_invoice.access_token:
                renewal_invoice._portal_ensure_token()

            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            payment_link = f"{base_url}/my/invoices/{renewal_invoice.id}?access_token={renewal_invoice.access_token}"

            subject = f"Membership Renewal Invoice {renewal_invoice.name}"
            body = f"""
                <p>Hello {membership.member_id.name},</p>
                <p>Your membership is due for renewal. Please pay the renewal invoice using the link below:</p>
                <p><a href="{payment_link}"> Pay Invoice Now</a></p>
                <p>Thank you!</p>
            """
            self.env["mail.mail"].create(
                {
                    "subject": subject,
                    "body_html": body,
                    "email_to": membership.email,
                }
            ).send()

            _logger.info(
                "> Renewal invoice %s created and email sent to %s",
                renewal_invoice.id,
                membership.email,
            )

    @api.model
    def _expire_unpaid_memberships(self):
        memberships = self.search(
            [
                ("state", "=", "active"),
                ("renewal_invoice_id.payment_state", "!=", "paid"),
            ]
        )

        _logger.info(">>> Checking memberships expiring in 7 days: %s", memberships)

        for member in memberships:
            unpaid_invoices = member.invoice_ids.filtered(
                lambda inv: inv.state == "posted" and inv.payment_state != "paid"
            )

            if unpaid_invoices:
                member.state = "expired"

                user = member.member_id.user_id

                if user:
                    user.active = False
                    _logger.info(
                        ">>> Deactivated user: %s for membership: %s",
                        user.login,
                        member.name,
                    )
                else:
                    _logger.warning(">>> No user linked to membership: %s", member.name)
                    _logger.info(
                        ">>> Membership '%s' expired due to unpaid invoice(s)",
                        member.name,
                    )
                if user.email:
                    mail_body = f"""
                            <p>Hello {user.name},</p>
                            <p>Your membership <b>{member.name}</b> is expired due to unpaid invoices.</p>
                            <p>Your user account has been deactivated. Please renew your membership to reactivate it.</p>
                            <br/><p>Regards,<br/>Membership Team</p>
                        """
                    try:
                        mail = self.env["mail.mail"].create(
                            {
                                "subject": "Membership Expired - Account Deactivated",
                                "body_html": mail_body,
                                "email_to": user.email,
                                "email_from": self.env.user.email
                                or "noreply@example.com",
                            }
                        )
                        mail.send()
                        _logger.info(
                            ">>> Email sent to %s regarding membership expiry.",
                            user.email,
                        )
                    except Exception as e:
                        _logger.error(
                            ">>> Failed to send email to %s: %s", user.email, str(e)
                        )
                else:
                    _logger.warning(
                        ">>> No email found for user %s. Cannot send expiration notice.",
                        user.login,
                    )

    @api.depends("duration_id")
    def _compute_product_id(self):
        for record in self:
            record.product_id = (
                record.duration_id.product_id if record.duration_id else False
            )

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("membership.membership") or "New"
            )

        if not vals.get("member_id"):
            member = self.env["website.member"].search(
                [("user_id", "=", self.env.user.id)], limit=1
            )
            if member:
                vals["member_id"] = member.id

        return super(Membership, self).create(vals)

    def action_request(self):
        for record in self:
            record.state = "request"

    def action_confirm(self):
        for record in self:
            record.state = "confirm"

    def action_create_invoice(self):
        for record in self:
            invoice = self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": record.member_id.partner_id.id,
                    "membership_date": record.membership_date,
                    "expiry_date": record.expiry_date,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": record.product_id.id,
                                "quantity": 1,
                                "price_unit": record.membership_fees,
                            },
                        )
                    ],
                    "membership_id": record.id,
                }
            )
            record.invoice_ids = [(4, invoice.id)]
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "view_mode": "form",
                "res_id": invoice.id,
            }

    def action_activate(self):
        for record in self:
            active_memberships = self.search(
                [
                    ("member_id", "=", record.member_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id),
                ]
            )
            if active_memberships:
                raise UserError(
                    f"The member {record.member_id.name} already has an active membership."
                )
            if not record.invoice_ids:
                raise UserError("create invoice before activating the membership.")
            paid_invoices = record.invoice_ids.filtered(
                lambda inv: inv.payment_state == "paid"
            )
            if not paid_invoices:
                raise UserError(
                    "cannot activate the membership until the invoice is paid."
                )
            record.state = "active"

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    def action_open_invoices(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("membership_id", "=", self.id)],
        }

    def action_expire(self):
        for record in self:
            if record.state != "active":
                raise UserError("Only active memberships can be expired.")
            record.state = "expired"


class AccountMove(models.Model):
    _inherit = "account.move"

    membership_id = fields.Many2one("membership.membership", string="Membership")
