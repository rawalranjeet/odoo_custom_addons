from odoo import api, fields, _, models
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    magento_instance_id = fields.Many2one("magento.instance")
    magento_sku_id = fields.Char()

    sync_to_magento = fields.Boolean()


    def write(self, vals):
        
        if vals.get('from_magento_operation'):
            del vals['from_magento_operation']

            return super(ProductTemplate, self).write(vals)
        

        res = super(ProductTemplate, self).write(vals)

        for product_template in self:
            if product_template.magento_sku_id and product_template.magento_instance_id:
                result = product_template.magento_instance_id.magento_update_product(product_template, vals)
                if not result:
                    raise UserError("Failed to update product in Magento")
                
            elif product_template.sync_to_magento and product_template.magento_instance_id and not product_template.magento_sku_id:
                result = product_template.magento_instance_id.magento_create_product(product_template)

                if not result:
                    raise UserError("Failed to create product in Magento")

                product_template.write({
                    'magento_sku_id': result.get('sku'),
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


        products = super().create(vals_list)

        if not from_magento_operation:

            for product in products:
                if product.sync_to_magento:
                    result = product.magento_instance_id.magento_create_product(product)

                    product.write({
                        'magento_sku_id': result.get('sku'),
                        'from_magento_operation': True,
                    })

        return products 



    def unlink(self):
        magento_sku_ids = []
        magento_instance_id = False

        for product in self:
            if product.magento_sku_id and product.magento_instance_id:
                magento_sku_ids.append(product.magento_sku_id)
                magento_instance_id = product.magento_instance_id

        res = super().unlink()

        
        if magento_sku_ids:
            result = magento_instance_id.magento_delete_products(magento_sku_ids)

            if result is False:
                raise UserError("Failed to delete product in Magento")

        return res

        # for product in self:
        #     if product.magento_sku_id and product.magento_instance_id:
        #         result = product.magento_instance_id.magento_delete_product(product)

        #         if result is False:
        #             raise UserError("Failed to delete product in Magento")

        # return super().unlink()
        
