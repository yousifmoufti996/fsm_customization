from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

class AddProductWizard(models.TransientModel):
    _name = 'add.product.wizard'
    _description = 'Add Product to FSM Order'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')
    qty_available = fields.Float(string='Available Quantity', related='product_id.qty_available', readonly=True)


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'fsm_order_id' in fields_list and self.env.context.get('fsm_order_id'):
            res['fsm_order_id'] = self.env.context.get('fsm_order_id')
        return res
    
    @api.constrains('quantity')
    def _check_quantity_available(self):
        for wizard in self:
            if (wizard.quantity > wizard.qty_available ) or (wizard.qty_available == 0):
                raise ValidationError(
                    _('Cannot add quantity %s. Only %s available in stock.') % 
                    (wizard.quantity, wizard.qty_available)
                )

    def action_add_product(self):
        """Add product to FSM order and create/update sale order"""
        if self.fsm_order_id and self.product_id:
            # Add product to FSM order
            self.fsm_order_id.write({
                'product_ids': [(4, self.product_id.id)]
            })
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Product "%s" added with quantity %s') % (self.product_id.name, self.quantity),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }