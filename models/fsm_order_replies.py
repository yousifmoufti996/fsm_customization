# Add this to your existing fsm_order.py file or create a new file

from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    reply_ids = fields.One2many(
        "fsm.order.reply", 
        "fsm_order_id", 
        string="Replies"
    )
    replies_count = fields.Integer(
        string="Replies Count", 
        compute="_compute_replies_count"
    )

    @api.depends("reply_ids")
    def _compute_replies_count(self):
        for order in self:
            order.replies_count = len(order.reply_ids)

    

    def action_view_replies(self):
        """Action to view all replies for this order"""
        return {
            'name': _('Order Replies'),
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order.reply',
            'view_mode': 'tree,form',
            'domain': [('fsm_order_id', '=', self.id)],
            'context': {
                'default_fsm_order_id': self.id,
                'default_agent_id': self.env.user.id,
            }
        }

