from odoo import api, _, fields, models
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    magento_customer_id = fields.Char()
    magento_instance_id = fields.Many2one("magento.instance")
    magento_address_id = fields.Integer()

    sync_to_magento = fields.Boolean()

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    
    dob = fields.Date('Date of Birth')


    def write(self, vals):

        if vals.get('from_import_operation'):
            del vals['from_import_operation']
            return super(ResPartner, self).write(vals)
        elif not vals: 
            return super(ResPartner, self).write(vals)
        

        res = super(ResPartner, self).write(vals)            
        

        for partner in self:
            if partner.magento_customer_id and partner.magento_instance_id:
                result = partner.magento_instance_id.magento_update_customer(partner, vals)

                if not result:
                    raise UserError("Failed to update Customer in Magento")
                
            elif partner.magento_address_id and partner.magento_instance_id:
                result = partner.magento_instance_id.magento_update_customer_address(partner, vals)

                if not result:
                    raise UserError("Failed to update Customer Address in Magento")
                

        return res
    

    @api.model_create_multi
    def create(self, vals_list):
        from_import_operation = False

        for vals in vals_list:
            if vals.get('from_import_operation'):
                from_import_operation = True
                del vals['from_import_operation']

        partners = super().create(vals_list)

        if from_import_operation:
            return partners

        for partner in partners:
            if partner.sync_to_magento:
                result = partner.magento_instance_id.magento_create_customer(partner)

                partner.magento_customer_id = result.get('id')

        return partners
    