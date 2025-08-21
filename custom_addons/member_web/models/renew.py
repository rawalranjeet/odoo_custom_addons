from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"
    membership_id = fields.Many2one("membership.membership", string="Membership")
    is_renewal_invoice = fields.Boolean(string="Is Renewal Invoice", default=False)

    membership_renewed_email_sent = fields.Boolean(
        string="Renewal Email Sent", default=False
    )

    @api.model
    def _cron_send_renewal_emails(self):
        _logger.info(">>> Running membership renewal mail cron")

        today = fields.Date.today()
        date_limit = today - timedelta(days=1)  # Only recent invoices

        invoices = self.search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "=", "paid"),
                ("invoice_date", ">=", date_limit),
                ("membership_id", "!=", False),
                ("is_renewal_invoice", "=", True),
                ("membership_renewed_email_sent", "=", False),
            ]
        )

        for invoice in invoices:
            membership = invoice.membership_id
            member = membership.member_id

            if not member.email:
                _logger.warning(
                    ">>> No email for member %s, skipping invoice %s",
                    member.name,
                    invoice.name,
                )
                continue

            subject = f"Membership Renewed - Invoice {invoice.name}"
            body = f"""
                <p>Hello {member.name},</p>
                <p>Your membership has been successfully renewed.</p>
                <p><strong>Membership Date:</strong> {invoice.membership_date.strftime('%m-%d-%y') if invoice.membership_date else 'N/A'}</p>
                <p><strong>Expiry Date:</strong> {invoice.expiry_date.strftime('%m-%d-%y') if invoice.expiry_date else 'N/A'}</p>
                <p>Thank you for staying with us!</p>
            """

            try:
                self.env["mail.mail"].create(
                    {
                        "subject": subject,
                        "body_html": body,
                        "email_to": member.email,
                        "email_from": self.env.user.email or "noreply@example.com",
                    }
                ).send()

                invoice.write({"membership_renewed_email_sent": True})

                _logger.info(
                    ">>> Sent renewal email to %s for invoice %s",
                    member.email,
                    invoice.name,
                )
            except Exception as e:
                _logger.error(
                    ">>> Error sending email to %s for invoice %s: %s",
                    member.email,
                    invoice.name,
                    str(e),
                )
