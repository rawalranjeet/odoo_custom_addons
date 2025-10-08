from odoo import models, fields, api
from odoo.http import request


class PropertyRoomEditNameWizard(models.TransientModel):
    _name = 'property.room.edit.name.wizard'
    _description = 'Edit Room Name Wizard'

    name = fields.Char("Name", required=True)

    def action_save_name_changes(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            record = self.env['property.room.room'].browse(active_id)
            record.write({
                'name': self.name,
            })
            
        return {'type': 'ir.actions.act_window_close'}

class PropertyEditNotesWizard(models.TransientModel):
    _name = 'property.edit.notes.wizard'
    _description = 'Edit Notes Wizard'
    
    notes = fields.Char("Notes")

    def action_save_notes_changes(self):
        active_id = self.env.context.get('active_id')
        property_id = request.session.get('selected_property_id')
        if property_id and active_id:
            room_line = self.env['property.room.line'].search([
                ('room_id', '=', active_id),
                ('property_id', '=', property_id)
            ], limit=1)
            room_line.write({
                'notes': self.notes,
            })
 
        return {'type': 'ir.actions.act_window_close'}
