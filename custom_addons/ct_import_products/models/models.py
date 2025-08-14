from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # brand_id = fields.Many2one('product.brand', string="Brand")
    # property_cost_method = fields.Selection([
    #     ('special_batch', 'Special - Batch')], string="Costing Method")
    length = fields.Float(string='Length')
    width = fields.Float(string='Width')
    height = fields.Float(string='Height')
    carton_length = fields.Float(string='Carton Length') 
    carton_width = fields.Float(string='Carton Width')
    carton_height = fields.Float(string='Carton Height')
    carton_inner_quantity = fields.Float(string='Carton Inner Quantity')
    carton_quantity = fields.Float(string='Carton Quantity')
    carton_volume = fields.Float(string='Carton Volume')
    # price_tier1 = fields.Float(string='Price Tier1')
    # price_tier2 = fields.Float(string='Price Tier2')
    # price_tier3 = fields.Float(string='Price Tier3')
    # price_tier4 = fields.Float(string='Price Tier4')
    # is_accounting_dimension_enabled = fields.Boolean('Is Accounting Dimension Enabled')
    # quantity_to_produce = fields.Integer('Quantity To Produce')
    # make_to_order_bom = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Make To Order Bom')
    # production_bom = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Production BOM')
    # always_show_quantity = fields.Integer('Always Show Quantity')
    # sellable = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Sellable')
    short_description = fields.Html(string='Short Description')
    # additional_attribute1 = fields.One2many('product.additional.attribute1', 'product_templ_id', string="Additional Attribute1")
    # additional_attribute2 = fields.One2many('product.additional.attribute2', 'product_templ_id', string="Additional Attribute2")
    # # average_cost = fields.Float('Average Cost')
    # inventory_account = fields.Many2one("account.account", string="Inventory Account")
    # COGSA_account = fields.Many2one('account.account', string="COGSAccount")


    @api.model
    def _get_volume_uom_id_from_ir_config_parameter(self):
        """ Get the unit of measure to interpret the `volume` field. By default, we consider
        that volumes are expressed in cubic meters. Users can configure to express them in cubic feet
        by adding an ir.config_parameter record with "product.volume_in_cubic_feet" as key
        and "1" as value.
        """
        # import pdb; pdb.set_trace()
        product_length_in_feet_param = self.env['ir.config_parameter'].sudo().get_param('product.volume_in_cubic_feet')
        if product_length_in_feet_param == '1':
            return self.env.ref('uom.product_uom_cubic_foot')
        else:
            return self.env.ref('uom.product_uom_cubic_meter')
            # return self.env.ref('ct_import_products.product_uom_cubic_new')
        

class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char("Brand Name", required=True)


class AdditionalAttribute1(models.Model):
    _name = 'product.additional.attribute1'

    name = fields.Char("Additional Attribute1")
    product_templ_id = fields.Many2one('product.template')


class AdditionalAttribute2(models.Model):
    _name = 'product.additional.attribute2'

    name = fields.Char("Additional Attribute2")
    product_templ_id = fields.Many2one('product.template')




