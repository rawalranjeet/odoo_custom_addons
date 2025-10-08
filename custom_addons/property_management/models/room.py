from odoo import models, fields, api
from odoo.http import request

class RoomComponentLine(models.Model):
    _name = 'property.room.component.line'
    _description = 'Room Component Lines'

    component_id = fields.Many2one('property.component.component', string="Component")
    room_line_id = fields.Many2one('property.room.line', string="Room Line")
    # quantity = fields.Integer(string='Quantity', default=1)
    length = fields.Integer(string='Length', default=8)
    height = fields.Integer(string='Height', default=8)
    preparation_ids = fields.Many2many(comodel_name='property.com.preparation.line')


class Room(models.Model):
    _name = 'property.room.room'
    _description = 'Room'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    is_added = fields.Boolean(string="Is Added", compute="_compute_is_added")
    quantity = fields.Integer(string='Quantity', default=1, compute="_compute_dimensions")
    height = fields.Integer(string='Height', default=8, compute="_compute_dimensions")
    width = fields.Integer(string="Width", default=8, compute="_compute_dimensions")
    length = fields.Integer(string="Length", default=8, compute="_compute_dimensions")
    notes = fields.Char(string="Notes", compute="_compute_dimensions")
    property_id = fields.Many2one('property.room.line', string="Property", readonly=True)
    property_name_char = fields.Char(string="Property Name", compute="_compute_property_name", store=False)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        compute="_compute_attachment_ids",
    )

    def action_upload_attachment(self):
        return True

    @api.model
    def create_attachment_from_kanban(self, res_id, attachment_ids):
        """Link uploaded attachments to the record immediately"""
        att_ids = attachment_ids and attachment_ids[0][2] or []  # Extract IDs from [(6, 0, [...])]
        if att_ids:
            attachments = self.env['ir.attachment'].browse(att_ids)
            attachments.write({
                'res_model': self._name,
                'res_id': res_id
            })
        return True


    def _compute_attachment_ids(self):
        for room in self:
            room.attachment_ids = False
            property_id = room.property_id.id if room.property_id else False
            if property_id:
                # )
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', room.property_id._name),
                    ('res_id', '=', property_id),
                ])
                if attachments:
                    room.attachment_ids = attachments.ids if attachments else False

    @api.depends('property_id')
    def _compute_property_name(self):
        for rec in self:
            property_id = request.session.get('selected_property_id')
            if property_id:
                prop = self.env['property.property'].browse(property_id)
                rec.property_name_char = prop.name or ''
            else:
                rec.property_name_char = ''

    def _get_room_line(self):
        self.ensure_one()
        property_id = request.session.get('selected_property_id')
        if not property_id:
            return None
        return self.env['property.room.line'].search([
            ('room_id', '=', self.id),
            ('property_id', '=', property_id)
        ], limit=1)

    def action_increase_height(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line:
                room_line.height += 1

    def action_decrease_height(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line and room_line.height > 0:
                room_line.height -= 1

    def action_increase_quantity(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line:
                room_line.quantity += 1

    def action_decrease_quantity(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line and room_line.quantity > 0:
                room_line.quantity -= 1

    def action_increase_width(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line:
                room_line.width += 1

    def action_decrease_width(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line and room_line.width > 0:
                room_line.width -= 1

    def action_increase_length(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line:
                room_line.length += 1

    def action_decrease_length(self):
        for record in self:
            room_line = record._get_room_line()
            if room_line and room_line.length > 0:
                room_line.length -= 1

    def _compute_is_added(self):
        for room in self:
            room.is_added = False
            property_id = request.session.get('selected_property_id')
            if property_id:
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room.id),
                    ('property_id', '=', property_id)
                ], limit=1)
                if room_line:
                    room.is_added = True

    def select_components(self):
        if self.is_added:
            request.session['selected_room_id'] = self.id
            return self.env.ref('property_management.action_room_component_kanban').read()[0]
        else:
            return True
    
    def add_property_room(self):
        for room in self:
            if not room.is_added:
                property_id = request.session.get('selected_property_id')
                property = self.env['property.property'].browse(property_id)
                if property:
                    room_line = self.env['property.room.line'].create({
                        'room_id': room.id,
                        'property_id': property.id,
                        'height': property.height
                        # 'quantity': property.quantity,
                        })
                    # room.property_id = room_line.id
                    
    def _compute_dimensions(self):
        for room in self:
            room.height = 0
            room.width = 0
            room.length = 0
            room.quantity = 0
            room.notes = ''
            room.property_id = False
            property_id = request.session.get('selected_property_id')
            if property_id:
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room.id),
                    ('property_id', '=', property_id)
                ], limit=1)
                if room_line:
                    room.height = room_line.height
                    room.width = room_line.width
                    room.length = room_line.length
                    room.quantity = room_line.quantity
                    room.notes = room_line.notes
                    room.property_id = room_line.id

    def add_component_services(self):
        property_id = request.session.get('selected_property_id')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.component.service',
            'view_mode': 'form',
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_order_id' : self.env.context.get('order_id'),
                'default_property_id': property_id
            },
            'target': 'new'
        }

    def action_open_edit_name_wizard(self):
        return {
            'name': "Edit Room Name",
            'type': 'ir.actions.act_window',
            'res_model': 'property.room.edit.name.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_name': self.name},
        }
    
    def action_open_edit_notes_wizard(self):
        return {
            'name': "Edit Notes",
            'type': 'ir.actions.act_window',
            'res_model': 'property.edit.notes.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_notes': self.notes},
        }