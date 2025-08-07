from odoo import fields, models, api, _

class FSMOrderLine(models.Model):
    _name = 'fsm.order.line'
    _description = 'FSM Order Line'

    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', readonly=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit