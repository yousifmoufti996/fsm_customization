from odoo import fields, models


class FSMOperationType(models.Model):
    _name = "fsm.operation.type"
    _description = "Field Service Operation Type"
    _order = "sequence, name"

    name = fields.Char(string="Operation Type", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
    
    # Relation to operation (fsm.order.type)
    operation_id = fields.Many2one(
        "fsm.order.type", 
        string="Operation", 
        required=True,
        ondelete="cascade"
    )
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('name_operation_uniq', 'unique (name, operation_id)', 
         'Operation Type name must be unique per Operation!')
    ]