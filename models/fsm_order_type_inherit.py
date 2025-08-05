from odoo import fields, models, api

class FSMOrder(models.Model):
    _inherit = "fsm.order"

    # Add the new operation_type field
    operation_type_id = fields.Many2one(
        "fsm.operation.type",
        string="Operation Type",
        domain="[('operation_id', '=', type)]"
    )

    @api.onchange('type')
    def _onchange_operation_clear_operation_type(self):
        """Clear operation type when operation changes"""
        if self.type:
            self.operation_type_id = False
            
            
class FSMOrderType(models.Model):
    _inherit = "fsm.order.type"

    # Add One2many relation to operation types
    operation_type_ids = fields.One2many(
        "fsm.operation.type",
        "operation_id",
        string="Operation Types"
    )
    
    operation_type_count = fields.Integer(
        string="Operation Types Count",
        compute="_compute_operation_type_count"
    )

    def _compute_operation_type_count(self):
        for record in self:
            record.operation_type_count = len(record.operation_type_ids)
            
            
    