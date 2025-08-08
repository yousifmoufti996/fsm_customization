from odoo import api, fields, models, _


class AreaNumber(models.Model):
    _name = "area.number"
    _description = "Area Number"
    
    name = fields.Char(string="رقم المنطقة", required=True)
    area_name_id = fields.Many2one(
        "area.name",
        string="اسم المنطقة",
        required=True
    )