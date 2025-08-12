from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

class AddProductWizard(models.TransientModel):
    _name = 'add.product.wizard'
    _description = 'Add Product to FSM Order'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')
    qty_available = fields.Float(string='Available Quantity', related='product_id.qty_available', readonly=True)












    @api.constrains('quantity')
    def _check_quantity_available(self):
        for wizard in self:
            if (wizard.quantity > wizard.qty_available ) or (wizard.qty_available == 0):
                raise ValidationError(
                    _('Cannot add quantity %s. Only %s available in stock.') % 
                    (wizard.quantity, wizard.qty_available)
                )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'picking_type_id' in fields_list and not res.get('picking_type_id'):
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            res['picking_type_id'] = warehouse.out_type_id.id
        if 'fsm_order_id' in fields_list and self.env.context.get('fsm_order_id'):
            res['fsm_order_id'] = self.env.context.get('fsm_order_id')
        return res
    
    def action_add_product(self):
        """Add product to FSM order and create/update sale order"""
        if self.fsm_order_id and self.product_id:
            
            # Create order line instead of just adding to many2many
            self.env['fsm.order.line'].create({
                'fsm_order_id': self.fsm_order_id.id,
                'product_id': self.product_id.id,
                'quantity': self.quantity,
            })
            
            
            # Create or update sale order
            self._create_or_update_sale_order()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Product "%s" added and sale order updated') % self.product_id.name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
            # Add product to FSM order
            # self.fsm_order_id.write({
            #     'product_ids': [(4, self.product_id.id)]
            # })
            
            # # Show success message
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': _('Success'),
            #         'message': _('Product "%s" added with quantity %s') % (self.product_id.name, self.quantity),
            #         'type': 'success',
            #         'sticky': False,
            #         'next': {'type': 'ir.actions.act_window_close'},
            #     }
            # }
            
    def _create_or_update_sale_order(self):
        """Create or update the sale order"""
        if not self.fsm_order_id.sale_order_id:
            # Create new sale order
            sale_order_vals = {
                'partner_id': self.fsm_order_id.location_id.partner_id.id,
                'origin': self.fsm_order_id.name,
            }
            sale_order = self.env['sale.order'].create(sale_order_vals)
            self.fsm_order_id.sale_order_id = sale_order.id
        
        # Add product line to existing sale order
        self.env['sale.order.line'].create({
            'order_id': self.fsm_order_id.sale_order_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': self.product_id.list_price,
        })