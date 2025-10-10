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
        
        
        if self.env.context.get('from_magento_operation'):
            return super().write(vals)
        elif not vals or vals.get('magento_address_id') or vals.get('magento_customer_id'):  
            return super().write(vals)
        

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

                partner.with_context(from_magento_operation = True).write({
                    'magento_customer_id': result.get('id'),
                })

                addresses = result.get('addresses')

                for address in addresses:
                
                    child_partner = self.env['res.partner'].search([('parent_id','=', partner.id),('magento_address_id','=',address.get('id'))])

                    country = self.env['res.country'].search([('code', '=', address.get('country_id'))])

                    if address.get('region').get('region') != None and country:
                        if address.get('region_id') == 0:
                            state = self.env['res.country.state'].search([('name','=', address.get('region').get('region')), ('country_id','=',country.id)])
                        else:
                            state = self.env['res.country.state'].search([('code','=', address.get('region').get('region_code')), ('country_id','=',country.id)])
                    else:
                        state = False

                    full_name = address.get('firstname') + " "

                    if address.get('middlename'):
                        full_name += (address.get('middlename') + " ")

                    full_name += address.get('lastname')
                    

                    child_vals =  {
                        "name" : full_name,
                        'magento_address_id': address.get('id'),
                        "magento_instance_id": self.magento_instance_id.id,
                        'phone': address.get('telephone'),
                        'parent_id': partner.id,
                        'street': address.get('street')[0],
                        'street2': address.get('street')[1] if len(address.get('street'))>1 else '',
                        'zip': address.get('postcode'),
                        'country_id': country.id if country else False,
                        'city': address.get('city'),
                        'state_id': state.id if state else False,
                        'sync_to_magento': True,
                        'type': 'delivery' if address.get('default_shipping') else 'invoice' if address.get('default_billing') else 'other',
                    }


                    if not child_partner:
                        child_partner.with_context(from_magento_operation = True).create(child_vals)
                    else:
                        child_partner.with_context(from_magento_operation = True).write(child_vals)
                

        return res
    


    def unlink(self):
        
        if self.env.context.get('from_magento_operation'):
            return super().unlink()
        
        for partner in self:
            if partner.magento_customer_id and partner.magento_instance_id and not partner.parent_id and partner.sync_to_magento:
                result = partner.magento_instance_id.magento_delete_customer(partner)

                if result is False:
                    raise UserError("Failed to delete Customer in Magento")

        return super().unlink()
    

    # Commented this because the odoo calls the write method whenever we create the a partner (so it will be handled in write method, avoid duplicate api calls)
    # @api.model_create_multi
    # def create(self, vals_list):

       
    #     partners = super().create(vals_list)

    #     if not self.env.context.get('from_magento_operation'):

    #         for partner in partners:
    #             if partner.sync_to_magento:
    #                 result = partner.magento_instance_id.magento_create_customer(partner)

    #                 partner.with_context(from_magento_operation = True).write({
    #                     'magento_customer_id': result.get('id'),
    #                 })

    #     return partners