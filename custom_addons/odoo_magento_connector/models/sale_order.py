from odoo import api, _, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    magento_order_id = fields.Char()
    magento_instance_id = fields.Many2one("magento.instance")



