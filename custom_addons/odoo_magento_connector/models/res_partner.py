from odoo import api, _, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    magento_customer_id = fields.Char()
    magento_instance_id = fields.Many2one("magento.instance")

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    
    dob = fields.Date('Date of Birth')

    
    