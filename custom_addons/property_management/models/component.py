from odoo import models, fields, api
from odoo.http import request

class ComponentPreparationLine(models.Model):
    _name = 'property.com.preparation.line'
    _description = 'Component Preparation Line'
    _inherit = ['mail.thread']

    name = fields.Char(string="Item")
    component_line_id = fields.Many2one('property.room.component.line', string="Component Line")
    room_line_id = fields.Many2one('property.room.line', string="Room Line")
    preparation_type = fields.Selection(string='Type',
                                        selection=[('sqft', 'SqFt'), ('linear', 'Linear'), ('count', 'Count')])
    # min = fields.Integer(string='Min')
    # max = fields.Integer(string='Max')
    default = fields.Integer(string='Default')
    feet = fields.Integer(string='Feet', default=lambda self: self._default_feet())
    sqft = fields.Integer(string='SqFt', default=lambda self: self.default)
    unit_type = fields.Integer(string='Count', default=lambda self: self.default)
    preparation_ids = fields.Many2many(comodel_name='property.preparation')
    attachment_ids = fields.Many2many(
        "ir.attachment",
        compute="_compute_attachment_ids",
        string="Attachments"
    )
    unit = fields.Char(string="Unit")
    quantity = fields.Integer(string='Quantity', default=1)

    def _compute_attachment_ids(self):
        for record in self:
            if record.id:
                record.attachment_ids = self.env["ir.attachment"].search([
                    ("res_model", "=", "property.com.preparation.line"),
                    ("res_id", "=", record.id)
                ])
            else:
                record.attachment_ids = False

class Components(models.Model):
    _name = 'property.component.component'
    _description = 'Components'
    _rec_name = 'name'

    name = fields.Char(required=True)
    length = fields.Integer(default=8)
    height = fields.Integer(default=8)
    is_added = fields.Boolean(string="Is Added", compute="_compute_is_added")
    preparation_ids = fields.Many2many(comodel_name='property.com.preparation.line')
    measurement_type = fields.Selection([
        ('sqft', 'Sqft'),
        ('count', 'Count'),
        ('linear', 'Linear')
    ], string="Measurement Type", default='sqft', required=True)
    int_or_ext = fields.Selection([
        ('int', 'Interior'),
        ('ext', 'Exterior')
    ], string="Int or Ext", default='int', required=True)
    component_type = fields.Many2one('property.component.type',string='Component Type')
    sqft = fields.Integer(string="Sqft")
    unit = fields.Integer(string="Unit")
    feet = fields.Integer(string="Feet")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    room_line_id = fields.Many2one('property.room.line', string="Room Line", readonly=True)
    room_line_char = fields.Char(string="Room Line ID (Char)", compute="_compute_room_line_name", store=False)

    @api.depends('room_line_id')
    def _compute_room_line_name(self):
        for rec in self:
            property_id = request.session.get('selected_property_id')
            room_id = request.session.get('selected_room_id')

            if property_id:
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room_id),
                    ('property_id', '=', property_id)
                ], limit=1)
                rec.room_line_char = room_line.room_id.name or ''

            else:
                rec.room_line_id = False
                rec.room_line_char = ''

    def _get_component_line(self):
        self.ensure_one()
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        if not (property_id and room_id):
            return None
        room_line = self.env['property.room.line'].search([
            ('room_id', '=', room_id),
            ('property_id', '=', property_id)
        ], limit=1)
        if not room_line:
            return None
        component_line = self.env['property.room.component.line'].search([
            ('component_id', '=', self._origin.id),
            ('room_line_id', '=', room_line.id)
        ], limit=1)
        return component_line

    def increase_length(self):
        for rec in self:
            line = rec._get_component_line()
            if line:
                line.length += 1

    def decrease_length(self):
        for rec in self:
            line = rec._get_component_line()
            if line and line.length > 0:
                line.length -= 1

    def increase_height(self):
        for rec in self:
            line = rec._get_component_line()
            if line:
                line.height += 1

    def decrease_height(self):
        for rec in self:
            line = rec._get_component_line()
            if line and line.height > 0:
                line.height -= 1

    def increase_sqft(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec:
                rec.sqft += 1
    
    def decrease_sqft(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec and rec.sqft > 0:
                rec.sqft -= 1

    def increase_feet(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec:
                rec.feet += 1
    
    def decrease_feet(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec and rec.feet > 0:
                rec.feet -= 1
    
    def increase_unit(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec:
                rec.unit += 1
    
    def decrease_unit(self):
        for rec in self:
            # line = rec._get_component_line()
            if rec and rec.unit > 0:
                rec.unit -= 1

    def _compute_is_added(self):
        for component in self:
            component.is_added = False
            property_id = request.session.get('selected_property_id')
            room_id = request.session.get('selected_room_id')
            if property_id:

                room_line = self.env['property.room.line'].search([
                    ('component_line_ids.component_id', '=', component.id),
                    ('property_id', '=', property_id),
                    ('room_id', '=', room_id)
                ], limit=1)
                component_line = self.env['property.room.component.line'].search([
                    ('component_id', '=', component.id),
                    ('room_line_id', '=', room_line.id)
                ], limit=1)

                if component_line:
                    component.is_added = True
                    component_preparation_line = self.env['property.com.preparation.line'].search([
                        ('component_line_id', '=', component_line.id),
                        ('room_line_id', '=', room_line.id)
                    ])
                    if component_preparation_line:
                        for com_pre_line in component_preparation_line:
                            component.preparation_ids = [(4, com_pre_line.id)]
                    else:
                        component.preparation_ids = False

                    for line in room_line.component_line_ids:
                        if line.component_id.id == component.id:
                            component.length = line.length
                            component.height = line.height
                            # component.preparation_ids = line.preparation_ids
                            break
                        else:
                            component.length = 8
                            component.height = 8
                            # component.preparation_ids = False
                else:
                    component.length = 8
                    component.height = 8
                    # component.preparation_ids = False

    def add_component(self):
        for component in self:
            if not component.is_added:
                property_id = request.session.get('selected_property_id')
                room_id = request.session.get('selected_room_id')
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room_id),
                    ('property_id', '=', property_id)
                ], limit=1)
                if room_line:
                    self.env['property.room.component.line'].create({
                        'component_id': component.id,
                        'room_line_id': room_line.id,
                        'length': component.length,
                        'height': component.height
                    })

    @api.onchange('length', 'height')
    def _onchange_length_height(self):
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        room_line = self.env['property.room.line'].search([
            ('room_id', '=', room_id),
            ('property_id', '=', property_id)
        ], limit=1)
        if room_line:
            component_line = self.env['property.room.component.line'].search([
                ('component_id', '=', self._origin.id),
                ('room_line_id', '=', room_line.id)
            ], limit=1)
            if component_line:
                component_line.write({
                    'length': self.length,
                    'height': self.height
                })

    def open_component(self):
        if self.is_added:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'property.component.component',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new'
            }
        else:
            return True

    def action_open_preparation(self):
        request.session['current_component_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Property Preparation',
            'res_model': 'property.preparation',
            'view_mode': 'kanban',
            'target': 'current',
        }

    def add_component_services(self):
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.component.service',
            'view_mode': 'form',
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_order_id' : self.env.context.get('order_id'),
                'default_property_id': property_id,
                'default_component_id': self.id,
                'default_room_ids': [(6, 0, [room_id])] if room_id else False,
                'default_from_component': True,
            },
            'target': 'new'
        }