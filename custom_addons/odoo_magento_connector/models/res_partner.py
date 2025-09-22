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
        
        
        if vals.get('from_magento_operation'):
            del vals['from_magento_operation']
            return super(ResPartner, self).write(vals)
        elif not vals or vals.get('magento_address_id'):  
            return super(ResPartner, self).write(vals)
        

        res = super(ResPartner, self).write(vals)            
        

        for partner in self:
            if partner.magento_customer_id and partner.magento_instance_id:

                result = partner.magento_instance_id.magento_update_customer(partner, vals)

                if not result:
                    raise UserError("Failed to update Customer in Magento")

                elif len(result.get('addresses')) == len(partner.child_ids):
                    
                    for i, address in enumerate(result.get('addresses')):
                        if partner.child_ids[i].magento_address_id != address.get('id'):
                            partner.child_ids[i].magento_address_id = address.get('id')

                
                
            elif partner.magento_address_id and partner.parent_id.magento_instance_id and partner.parent_id.magento_customer_id:
                
                result = partner.parent_id.magento_instance_id.magento_update_customer(partner.parent_id, vals)

                if not result:
                    raise UserError("Failed to update Customer Address in Magento")
                
            elif partner.sync_to_magento and partner.magento_instance_id and not partner.magento_customer_id and not partner.parent_id:
                result = partner.magento_instance_id.magento_create_customer(partner)

                if not result:
                    raise UserError("Failed to create customer in Magento")

                partner.write({
                    'magento_customer_id': result.get('id'),
                    'from_magento_operation': True,
                })
                

        return res
    

    @api.model_create_multi
    def create(self, vals_list):
        from_magento_operation = False

        for vals in vals_list:
            if vals.get('from_magento_operation'):
                from_magento_operation = True
                del vals['from_magento_operation']


        partners = super().create(vals_list)

        if not from_magento_operation:

            for partner in partners:
                if partner.sync_to_magento:
                    result = partner.magento_instance_id.magento_create_customer(partner)

                    partner.magento_customer_id = result.get('id')

        return partners
    

    def unlink(self):
        for partner in self:
            if partner.magento_customer_id and partner.magento_instance_id and not partner.parent_id and partner.sync_to_magento:
                result = partner.magento_instance_id.magento_delete_customer(partner)

                if result is False:
                    raise UserError("Failed to delete Customer in Magento")

        return super(ResPartner, self).unlink()
    