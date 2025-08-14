from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'
    _description = 'Maintenance Equipment'

    schedule = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('anually', 'Anually')
    ], string='Schedule')

    parts = fields.One2many('ct.equipment.parts', 'equipment_id', string='Parts')
    check_rollers_for_wear = fields.Boolean("Check Rollers for Wear")
    clean_out_of_debri = fields.Boolean("Clean out of Debri from underneath")
    check_cable_for_any_fraying = fields.Boolean("Check Cable for any fraying")
    check_power_wires = fields.Boolean("Check Power Cord for any cuts or exposed Wires")

    clean_battery_compartments = fields.Boolean("Clean battery compartments thoroughly")
    free_of_corrosion_and_damage = fields.Boolean("Battery cables and connectors free of corrosion and damage")
    inspect_drive_unit = fields.Boolean("Inspect drive unit for leaks and unusual noises")
    check_chain_stretch = fields.Boolean("Check chain stretch and adjust if needed")
    lubricate_mast_chains = fields.Boolean("Lubricate mast chains, as recommended")
    inspect_hydraulic_oil = fields.Boolean("Inspect hydraulic oil reservoir level and refill if necessary")
    clean_and_inspect = fields.Boolean("Clean and inspect all electrical connections")
    inspect_caster = fields.Boolean("Inspect caster and load wheels for wear")
    inspect_brake_pads = fields.Boolean("Inspect brake pads for wear and proper adjustment")
    inspect_all_hydraulic_cylinders = fields.Boolean("Inspect all hydraulic cylinders for leaks or wear")
    grease_all_specified_fittings = fields.Boolean("Grease all specified fittings")
    test_for_unusual_noises = fields.Boolean("Test for unusual noises during operation")
    tighten_all_hardware = fields.Boolean("Tighten all hardware to manufacturer specs")
    check_structural_welds = fields.Boolean("Check structural welds for cracks or separation")
    verify_mast_alignment_load = fields.Boolean("Verify mast alignment and operation under load")
    inspect_operator_compartment = fields.Boolean("Inspect operator compartment floor mat for damage or wear")


class EquipmentParts(models.Model):
    _name = 'ct.equipment.parts'

    name = fields.Char()
    equipment_id = fields.Many2one('maintenance.equipment')
    partner_id = fields.Many2one('res.partner', string='Parts/Vendor')
    serial_no = fields.Char('Item Number')
