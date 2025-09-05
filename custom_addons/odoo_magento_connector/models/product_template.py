from odoo import api, fields, _, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    magento_instance_id = fields.Many2one("magento.instance")
    magento_sku_id = fields.Char()
