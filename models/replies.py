from odoo import api, fields, models


class FSMOrderReply(models.Model):
    _name = "fsm.order.reply"
    _description = "Field Service Order Reply"
    _order = "create_date desc"
    _rec_name = "text"

    fsm_order_id = fields.Many2one(
        "fsm.order", 
        string="FSM Order", 
        required=True, 
        ondelete="cascade"
    )
    agent_id = fields.Many2one(
        "res.users", 
        string="Agent", 
        default=lambda self: self.env.user,
        required=True
    )
    text = fields.Text(string="Reply Text", required=True)


    action_id = fields.Many2one(
        "fsm.reply.action", 
        string="Action",
        required=False
    )
    
    create_date = fields.Datetime(string="Added On", readonly=True)
    
    @api.model
    def create(self, vals):
        if not vals.get('create_date'):
            vals['create_date'] = fields.Datetime.now()
        return super().create(vals)