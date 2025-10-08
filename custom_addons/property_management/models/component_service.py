from email.policy import default

from odoo import models, fields, api

class ComponentService(models.Model):
    _name = 'property.component.service'
    _description = 'Component Services'

    order_id = fields.Many2one('sale.order', string="Sale Order")
    property_id = fields.Many2one('property.property', related="order_id.property_id")
    component_ids = fields.Many2many('property.component.component', string='Component', compute="_get_component_ids")
    component_id = fields.Many2one('property.component.component', string='Component', domain="[('id', 'in', component_ids)]")
    property_room_ids = fields.Many2many('property.room.room', 'property_room_component_service_rel', string='Rooms', compute="_get_property_room_ids")
    room_ids = fields.Many2many('property.room.room', string='Rooms', domain="[('id', 'in', property_room_ids)]")
    service_id = fields.Many2one('product.template', string="Service", domain="[('categ_id.category_type', '=', 'paint')]")
    sheen_id = fields.Many2one(
        'product.attribute.value',
        string="Sheen",
        domain="[('attribute_id.name', '=', 'Sheen'),('pav_attribute_line_ids.product_tmpl_id', '=', service_id)]"
    )
    color_id = fields.Many2one(
        'product.attribute.value',
        string="Color",
        domain="[('attribute_id.name', '=', 'Color'),('pav_attribute_line_ids.product_tmpl_id', '=', service_id)]"
    )
    coats = fields.Selection([
        ('guaranteed', 'Guaranteed Coverage'),
        ('1', '1'),
        ('2', '2')
    ], string='Coats', default='guaranteed')
    primer_id = fields.Many2one(
        'product.product', string='Primer',
        domain="[('categ_id.category_type', '=', 'primer')]"
    )
    primer_coats = fields.Selection([
        ('spot', 'Spot'),
        ('full', 'Full')
    ], string='Primer Coats')
    is_added_to_order = fields.Boolean(string="Is Added to Order")
    from_component = fields.Boolean(string="From Component",default=False)
    # note = fields.Char(string='Note',required=False)
    # int_note = fields.Char(string='Int.Note',required=False)


    @api.depends('order_id.property_id')
    def _get_component_ids(self):
        for rec in self:
            if rec.property_id:
                property_room_component_ids = []
                property_room_lines = self.env['property.room.line'].search([('property_id', '=', rec.property_id.id)])
                property_room_components = property_room_lines.mapped('component_line_ids').mapped('component_id')

                for component in property_room_components:
                    property_room_lines = self.env['property.room.line'].search([('property_id', '=', rec.property_id.id), ('component_line_ids.component_id', '=', component.id)])
                    property_component_order_lines = self.env['property.component.order.line'].search([('sale_order_id', '=', rec.order_id.id), ('component_id', '=', component.id)])
                    if (property_room_lines.mapped('room_id') - property_component_order_lines.mapped('rooms')):
                        property_room_component_ids.append(component.id)
                if rec.component_id:
                    property_room_lines = self.env['property.room.line'].search([('property_id', '=', rec.property_id.id), ('component_line_ids.component_id', '=', rec.component_id.id)])
                    if property_room_lines.mapped('room_id') == property_component_order_lines.mapped('rooms'):
                        property_room_component_ids.remove(rec.component_id.id)
                rec.component_ids = property_room_component_ids
            else:
                rec.component_ids = []

    @api.depends('component_id')
    def _get_property_room_ids(self):
        for rec in self:
            rec.property_room_ids = False
            if not self._origin.component_id:
                rec.room_ids = False
            if rec.component_id and rec.property_id:
                property_room_lines = self.env['property.room.line'].search([('property_id', '=', rec.property_id.id), ('component_line_ids.component_id', '=', rec.component_id.id)])
                property_component_order_lines = self.env['property.component.order.line'].search([('component_id', '=', rec.component_id.id), ('sale_order_id', '=', rec.order_id.id)])
                if property_room_lines:
                    property_rooms = property_room_lines.mapped('room_id') - property_component_order_lines.mapped('rooms')
                    rec.property_room_ids = property_rooms.ids or []
                else:
                    rec.property_room_ids = []
            else:
                rec.property_room_ids = []

    def add_to_sale_order(self):
        self.ensure_one()
        if not self.order_id:
            return {
                'warning': {
                    'title': 'No Sale Order',
                    'message': 'Please select a sale order to add the component service.'
                }
            }

        Line = self.env['property.component.order.line']
        order = self.order_id

        # === 1. Create new component lines ===
        for room in self.room_ids:
            Line.create({
                'sale_order_id': order.id,
                'component_id': self.component_id.id,
                'primer_product_id': self.primer_id.id,
                'paint_product_id': self.service_id.id,
                'rooms': room.id,
                'sheen_id': self.sheen_id.id,
                'color_id': self.color_id.id,
                'coats': self.coats,
                'primer_coats': self.primer_coats,
                # 'note': self.note,
                # 'int_note': self.int_note,
            })

        self.is_added_to_order = True

        # === 2. Re-group all lines by room (excluding sections) ===
        grouped = {}
        normal_lines = order.component_order_line_ids.filtered(lambda l: not l.display_type)

        for line in normal_lines:
            room_name = line.rooms.name or "None"
            grouped.setdefault(room_name, []).append(line)

        # === 3. Clear existing section lines (to avoid duplicates) ===
        order.component_order_line_ids.filtered(lambda l: l.display_type == 'line_section').unlink()

        # === 4. Rebuild sequence numbers ===
        seq = 1
        for room_name, lines in grouped.items():
            # create section line
            Line.create({
                'sale_order_id': order.id,
                'display_type': 'line_section',
                'name': room_name,
                'sequence': seq,
            })
            seq += 1

            # assign sequence to each data line of that room
            for line in lines:
                line.sequence = seq
                seq += 1

        # === 5. Return to the order form ===
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.depends('name')
    def _compute_display_name(self):
        for value in self:
            value.display_name = value.name