from odoo import models, fields, api


class CheckList(models.Model):
    _name = "maintenance.equipment.checklist"
    
    name = fields.Char()
    # equipment_id = fields.Many2one("maintenance.equipment")
    



class MaintenanceEquipmentCheckListConfiguration(models.Model):
    _name = "maintenance.equipment.checklist.configuration"

    equipment_id = fields.Many2one("maintenance.equipment")
    checklist_ids = fields.Many2many("maintenance.equipment.checklist", "equipment_checklist_rel7", "config_id", "checklist_id",string = "Check List")
    
    
    def generate_checklist_lines(self):
        ChecklistLine = self.env['maintenance.equipment.checklist.line']

        for config in self:
            if not config.equipment_id:
                continue

            for checklist in config.checklist_ids:
                # Check if already exists
                exists = ChecklistLine.search([
                    ('equipment_id', '=', config.equipment_id.id),
                    ('checklist_id', '=', checklist.id)
                ], limit=1)

                if not exists:
                    ChecklistLine.create({
                        'equipment_id': config.equipment_id.id,
                        'checklist_id': checklist.id,
                        'is_checked': False
                    })

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        records.generate_checklist_lines()
        return records

    def write(self, vals):
        res = super().write(vals)
        ChecklistLine = self.env['maintenance.equipment.checklist.line']

        for config in self:
            if not config.equipment_id:
                continue

            # Remove lines not in checklist_ids anymore
            existing_lines = ChecklistLine.search([
                ('equipment_id', '=', config.equipment_id.id)
            ])
            for line in existing_lines:
                if line.checklist_id not in config.checklist_ids:
                    line.unlink()

        self.generate_checklist_lines()
        return res

    def unlink(self):
        ChecklistLine = self.env['maintenance.equipment.checklist.line']
        for config in self:
            ChecklistLine.search([
                ('equipment_id', '=', config.equipment_id.id),
                ('checklist_id', 'in', config.checklist_ids.ids)
            ]).unlink()
        return super().unlink()

class MaintenanceEquipmentChecklistLine(models.Model):
    _name = "maintenance.equipment.checklist.line"
    _description = "Checklist Line per Equipment"

    equipment_id = fields.Many2one("maintenance.equipment", required=True, string="Equipment")
    checklist_id = fields.Many2one("maintenance.equipment.checklist", required=True, string="Checklist Item")
    is_checked = fields.Boolean(string="Checked", default=False)


    

# class MaintenanceEquipmentCheckList(models.Model):
#     _name = "maintenance.equipment.checklist"
    
#     name = fields.Char()
#     equipment_id = fields.Many2one("maintenance.equipment")
#     is_checked = fields.Boolean()



    # check_rollers_for_wear = fields.Boolean("Check Rollers for Wear")
    # clean_out_of_debri = fields.Boolean("Clean out of Debri from underneath")
    # check_cable_for_any_fraying = fields.Boolean("Check Cable for any fraying")
    # check_power_wires = fields.Boolean("Check Power Cord for any cuts or exposed Wires")
    # clean_battery_compartments = fields.Boolean("Clean battery compartments thoroughly")
    # free_of_corrosion_and_damage = fields.Boolean("Battery cables and connectors free of corrosion and damage")
    # inspect_drive_unit = fields.Boolean("Inspect drive unit for leaks and unusual noises")
    # check_chain_stretch = fields.Boolean("Check chain stretch and adjust if needed")
    # lubricate_mast_chains = fields.Boolean("Lubricate mast chains, as recommended")
    # inspect_hydraulic_oil = fields.Boolean("Inspect hydraulic oil reservoir level and refill if necessary")
    # clean_and_inspect = fields.Boolean("Clean and inspect all electrical connections")
    # inspect_caster = fields.Boolean("Inspect caster and load wheels for wear")
    # inspect_brake_pads = fields.Boolean("Inspect brake pads for wear and proper adjustment")
    # inspect_all_hydraulic_cylinders = fields.Boolean("Inspect all hydraulic cylinders for leaks or wear")
    # grease_all_specified_fittings = fields.Boolean("Grease all specified fittings")
    # test_for_unusual_noises = fields.Boolean("Test for unusual noises during operation")
    # tighten_all_hardware = fields.Boolean("Tighten all hardware to manufacturer specs")
    # check_structural_welds = fields.Boolean("Check structural welds for cracks or separation")
    # verify_mast_alignment_load = fields.Boolean("Verify mast alignment and operation under load")
    # inspect_operator_compartment = fields.Boolean("Inspect operator compartment floor mat for damage or wear")

