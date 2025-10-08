from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = "product.category"

    category_type = fields.Selection(
        [
            ('paint', 'Paint'),
            ('primer', 'Primer'),
            ('other', 'Other'),
        ],
        string="Category Type",
        default='other',
    )
