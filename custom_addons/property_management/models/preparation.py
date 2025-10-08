from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import UserError


class Preparation(models.Model):
    _name = 'property.preparation'
    _description = 'Preparation'
    _inherit = ['mail.thread']

    name = fields.Char(string="Item")
    preparation_type = fields.Selection(string='Type',selection=[('sqft', 'SqFt'),('linear', 'Linear'), ('count', 'Count')])
    # min =  fields.Integer(string='Min')
    # max = fields.Integer(string='Max')
    default = fields.Integer(string='Default')
    feet = fields.Integer(string='Feet',compute="_compute_is_added")
    sqft = fields.Integer(string='SqFt',compute="_compute_is_added")
    unit_type = fields.Integer(string='Count',compute="_compute_is_added")
    is_added = fields.Boolean(string="Is Added", compute="_compute_is_added", default=False, store=False)
    note = fields.Char(string='Note', required=False)
    int_note = fields.Char(string='Int.Note', required=False)
    component_line_ids = fields.Many2one('property.room.line', string="Component", readonly=True)
    component_name_char = fields.Char(string="Component Name", compute="_compute_component_name", store=False)
    com_preparation_line_id = fields.Many2one(
        comodel_name='property.com.preparation.line',
        required=False)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        compute="_compute_attachment_ids",
    )
    component_type = fields.Many2many('property.component.type',string='Component Type')
    unit = fields.Char(string='Unit',readonly=False)
    quantity = fields.Integer(string='Quantity', default=1,compute="_compute_is_added")


    def _compute_attachment_ids(self):
        for preparation in self:
            preparation.attachment_ids = False
            property_id = request.session.get('selected_property_id')
            if property_id:
                component_preparation_line = preparation._get_preparation_line()
                if component_preparation_line:
                    preparation.attachment_ids = component_preparation_line.attachment_ids if component_preparation_line else False

    def action_upload_attachment(self):
        return True

    @api.depends('component_line_ids')
    def _compute_component_name(self):
        for rec in self:
            component_id = request.session.get('current_component_id')
            if component_id:
                component = self.env['property.component.component'].browse(component_id)
                rec.component_name_char = component.name or ''
            else:
                rec.component_name_char = ''


    def _get_preparation_line(self):
        self.ensure_one()
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        current_component = request.session.get('current_component_id')

        if not (property_id and room_id):
            return None
        room_line = self.env['property.room.line'].search([
            ('room_id', '=', room_id),
            ('property_id', '=', property_id)
        ], limit=1)
        if not room_line:
            return None
        component_line = self.env['property.room.component.line'].search([
            ('component_id', '=', current_component),
            ('room_line_id', '=', room_line.id)
        ], limit=1)
        component_preparation_line = self.env['property.com.preparation.line'].search([
            ('component_line_id', '=', component_line.id),
            ('room_line_id', '=', room_line.id),
            ('preparation_ids', 'in', [self.id])
        ], limit=1)

        return component_preparation_line

    def _compute_is_added(self):
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        current_component = request.session.get('current_component_id')

        for rec in self:
            rec.feet = 0
            rec.sqft = 0
            rec.unit_type = 0
            # rec.unit = ''
            rec.quantity = 0
            rec.com_preparation_line_id = False
            rec.is_added = False  # Default
            if property_id and room_id and current_component:
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room_id),
                    ('property_id', '=', property_id)
                ], limit=1)

                if room_line:
                    component_line = self.env['property.room.component.line'].search([
                        ('component_id', '=', current_component),
                        ('room_line_id', '=', room_line.id)
                    ], limit=1)
                    component_preparation_line = self.env['property.com.preparation.line'].search([
                        ('component_line_id', '=', component_line.id),
                        ('room_line_id', '=', room_line.id),
                        ('preparation_ids', 'in', [rec.id])
                    ], limit=1)

                    if component_preparation_line:
                        rec.feet = component_preparation_line.feet
                        rec.sqft = component_preparation_line.sqft
                        rec.unit_type = component_preparation_line.unit_type
                        # rec.unit = component_preparation_line.unit
                        rec.quantity = component_preparation_line.quantity
                        rec.com_preparation_line_id = component_preparation_line.id
                        rec.is_added = True

    def add_preparation(self):
        property_id = request.session.get('selected_property_id')
        room_id = request.session.get('selected_room_id')
        current_component = request.session.get('current_component_id')

        for preparation in self:
            if not preparation.is_added:
                room_line = self.env['property.room.line'].search([
                    ('room_id', '=', room_id),
                    ('property_id', '=', property_id)
                ], limit=1)
                component_line = self.env['property.room.component.line'].search([
                    ('component_id', '=', current_component),
                    ('room_line_id', '=', room_line.id)
                ], limit=1)
                if component_line:
                    component_preparation_line_id = self.env['property.com.preparation.line'].create({
                        'component_line_id': component_line.id,
                        'room_line_id': room_line.id,
                        'preparation_type': preparation.preparation_type,
                        'name': preparation.name,
                        # 'min': preparation.min,
                        # 'max': preparation.max,
                        'default': preparation.default,
                        'feet': preparation.default,
                        'sqft': preparation.default,
                        'unit_type': preparation.default,
                        'quantity': 1,
                        'preparation_ids': [(4, self.id)]
                    })
                    component_line.write({
                        'preparation_ids': [(4, component_preparation_line_id.id)]
                    })

    # def open_preparation(self):
    #     return True

    # @api.onchange('min', 'max')
    # def _onchange_min_max(self):
    #     if self.min and self.max:
    #         if self.min > self.max:
    #             # raise UserError("Min value cannot be greater than Max value.")
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Validation Error',
    #                     'message': "Min value cannot be greater than Max value.",
    #                     'type': 'warning',
    #                     'sticky': False,
    #                 }
    #             }
    #         if self.max < self.min:
    #             # raise UserError("Max value cannot be less than Min value.")
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Validation Error',
    #                     'message': "Max value cannot be less than Min value.",
    #                     'type': 'warning',
    #                     'sticky': False,
    #                 }
    #             }

    # @api.onchange('default')
    # def _onchange_default(self):
    #     if self.default < self.min:
    #         # raise UserError("Default value cannot be less than Min value.")
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Validation Error',
    #                 'message': "Default value cannot be less than Min value.",
    #                 'type': 'warning',
    #                 'sticky': False,
    #             }
    #         }
    #     if self.default > self.max:
    #         # raise UserError("Default value cannot be greater than Max value.")
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Validation Error',
    #                 'message': "Default value cannot be greater than Max value.",
    #                 'type': 'warning',
    #                 'sticky': False,
    #             }
    #         }
    # def increase_min(self):
    #     for rec in self:
    #         if rec:
    #             if rec.max > rec.min:
    #                 rec.min += 1
    #             else:
    #                 # raise UserError("Min value cannot be greater than Max value.")
    #                 return {
    #                     'type': 'ir.actions.client',
    #                     'tag': 'display_notification',
    #                     'params': {
    #                         'title': 'Validation Error',
    #                         'message': "Min value cannot be greater than Max value.",
    #                         'type': 'warning',
    #                         'sticky': False,
    #                     }
    #                 }
    #
    #
    # def decrease_min(self):
    #     for rec in self:
    #         if rec and rec.min > 0:
    #             rec.min -= 1
    #
    # def increase_max(self):
    #     for rec in self:
    #         if rec:
    #             rec.max += 1
    #
    # def decrease_max(self):
    #     for rec in self:
    #         if rec and rec.max > 0 and rec.max > rec.min:
    #             rec.max -= 1
    #         else:
    #             # raise UserError("Max value cannot be less than Min value.")
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Validation Error',
    #                     'message': "Max value cannot be less than Min value.",
    #                     'type': 'warning',
    #                     'sticky': False,
    #                 }
    #             }

    def increase_default(self):
        for rec in self:
            if rec:
                rec.default += 1

    def decrease_default(self):
        for rec in self:
            if rec and rec.default > 0:
                rec.default -= 1

    def action_increase_quantity(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line:
                line.quantity += 1
            rec._compute_is_added()

    def action_decrease_quantity(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line and line.quantity > 0:
                line.quantity -= 1
            rec._compute_is_added()

    def increase_feet(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line:
                line.feet += 1
            rec._compute_is_added()
                # else:
                #     # raise UserError("Feet value cannot be greater than Max value.")
                #     return {
                #         'type': 'ir.actions.client',
                #         'tag': 'display_notification',
                #         'params': {
                #             'title': 'Validation Error',
                #             'message': "Feet value cannot be greater than Max value.",
                #             'type': 'warning',
                #             'sticky': False,
                #         }
                #     }

    def decrease_feet(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line and line.feet > 0:
                line.feet -= 1
            rec._compute_is_added()
            # else:
            #     # raise UserError("Feet value cannot be less than Min value.")
            #     return {
            #         'type': 'ir.actions.client',
            #         'tag': 'display_notification',
            #         'params': {
            #             'title': 'Validation Error',
            #             'message': "Feet value cannot be less than Min value.",
            #             'type': 'warning',
            #             'sticky': False,
            #         }
            #     }

    def increase_sqft(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line:
                line.sqft += 1
            rec._compute_is_added()
                # else:
                #     # raise UserError("Sqft value cannot be greater than Max value.")
                #     return {
                #         'type': 'ir.actions.client',
                #         'tag': 'display_notification',
                #         'params': {
                #             'title': 'Validation Error',
                #             'message': "Sqft value cannot be greater than Max value.",
                #             'type': 'warning',
                #             'sticky': False,
                #         }
                #     }

    def decrease_sqft(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line and line.sqft > 0:
                line.sqft -= 1
            rec._compute_is_added()
            # else:
            #     # raise UserError("Sqft value cannot be less than Min value.")
            #     return {
            #         'type': 'ir.actions.client',
            #         'tag': 'display_notification',
            #         'params': {
            #             'title': 'Validation Error',
            #             'message': "Sqft value cannot be less than Min value.",
            #             'type': 'warning',
            #             'sticky': False,
            #         }
            #     }

    def increase_unit(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line:
                line.unit_type += 1
            rec._compute_is_added()
                # else:
                #     # raise UserError("Count value cannot be greater than Max value.")
                #     return {
                #         'type': 'ir.actions.client',
                #         'tag': 'display_notification',
                #         'params': {
                #             'title': 'Validation Error',
                #             'message': "Unit value cannot be greater than Max value.",
                #             'type': 'warning',
                #             'sticky': False,
                #         }
                #     }

    def decrease_unit(self):
        for rec in self:
            line = rec._get_preparation_line()
            if line and line.unit_type > 0 :
                line.unit_type -= 1
            rec._compute_is_added()
            # else:
            #     # raise UserError("Count value cannot be less than Min value.")
            #     return {
            #         'type': 'ir.actions.client',
            #         'tag': 'display_notification',
            #         'params': {
            #             'title': 'Validation Error',
            #             'message': "Unit value cannot be less than Min value.",
            #             'type': 'warning',
            #             'sticky': False,
            #         }
            #     }



