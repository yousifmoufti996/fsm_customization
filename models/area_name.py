from odoo import api, fields, models, _

class AreaName(models.Model):

    
    _inherit = "area.name"

   
    area_number_ids = fields.One2many(
        "area.number",
        "area_name_id",
        string="أرقام المنطقة"
    )