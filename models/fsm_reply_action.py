# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMReplyAction(models.Model):
    _name = "fsm.reply.action"
    _description = "Field Service Reply Action"
    _order = "sequence, name"

    name = fields.Char(string="Action Name", required=True, translate=True)
    code = fields.Char(string="Action Code", help="Technical code for the action")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    color = fields.Integer(string="Color", default=0)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id)', 'Action name must be unique per company!'),
        ('code_company_uniq', 'unique (code, company_id)', 'Action code must be unique per company!'),
    ]

    def name_get(self):
        result = []
        for record in self:
            if record.code:
                name = f"[{record.code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result