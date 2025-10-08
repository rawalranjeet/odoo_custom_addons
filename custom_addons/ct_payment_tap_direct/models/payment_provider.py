# -*- coding: utf-8 -*-
import json
from odoo import _, fields, models


class PaymentProviderTap(models.Model):
    _inherit = 'payment.provider'

    def _tap_get_inline_form_values(self, **kwargs):
        """
        Return a serialized JSON of the required values to render the inline form.
        """
        self.ensure_one()
        return json.dumps({
            'publishable_key': self.tap_publishable_key,
        })