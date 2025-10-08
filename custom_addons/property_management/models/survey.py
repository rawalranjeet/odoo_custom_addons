from odoo import models, fields, api

class SurveyExtended(models.Model):
    _inherit = 'survey.survey'

    partner_id = fields.Many2one("res.partner", "Customer")
    sale_order_template_id = fields.Many2one("sale.order.template", "Sale Order Template")