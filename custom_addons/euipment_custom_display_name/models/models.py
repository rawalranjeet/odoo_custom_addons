from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    equipment_type = fields.Char("Equipment Type")
    checklist_lines = fields.One2many(comodel_name="maintenance.equipment.checklist.line", inverse_name="equipment_id", compute = '_compute_checklist_lines', readonly=False)


    @api.onchange('equipment_type')
    def _compute_display_name(self):
        for record in self:
            if record.equipment_type:
                record.display_name = (record.name or '') + '/' + record.equipment_type
            else:
                record.display_name = record.name
    

    def _compute_checklist_lines(self):
        # import pdb; pdb.set_trace()
        for record in self:
            record.checklist_lines = record.env['maintenance.equipment.checklist.line'].search([('equipment_id','=',record.id)])


    # def _compute_checklist_lines(self):
    #     # import pdb; pdb.set_trace()
    #     for equipment in self:
    #         config = self.env['maintenance.equipment.checklist.configuration'].search([
    #             ('equipment_id', '=', equipment.id)
    #         ], limit=1)
    #         if not config:
    #             equipment.checklist_lines = self.env['maintenance.equipment.checklist.line']
    #             continue

    #         checklist_items = config.checklist_ids
    #         lines = self.env['maintenance.equipment.checklist.line'].search([
    #             ('equipment_id', '=', equipment.id),
    #             ('checklist_id', 'in', checklist_items.ids)
    #         ])
    #         equipment.checklist_lines = lines

    #         # equipment.checklist_lines = config.checklist_ids