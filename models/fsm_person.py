# models/fsm_person.py
from odoo import fields, models

class FSMPerson(models.Model):
    _inherit = "fsm.person"
    
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Partner", 
        readonly=False,
        delegate=False  # Remove delegation
    )
    
    partner_selection_id = fields.Many2one(
        'res.partner',
        string='Select Partner',
        domain="[('is_company', '=', False)]"
    )