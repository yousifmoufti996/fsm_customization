from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

class AddProductWizard(models.TransientModel):
    _name = 'add.product.wizard'
    _description = 'Add Product to FSM Order'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')
    qty_available = fields.Float(string='Available Quantity', related='product_id.qty_available', readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type')

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
            if warehouse:
                res['picking_type_id'] = warehouse.out_type_id.id
        if 'fsm_order_id' in fields_list and self.env.context.get('fsm_order_id'):
            res['fsm_order_id'] = self.env.context.get('fsm_order_id')
        return res
    
    def action_add_product(self):
        """Add product to FSM order and create/update sale order"""
        if self.fsm_order_id and self.product_id:
            
            # Add product to FSM order's product_ids Many2many field
            if self.product_id not in self.fsm_order_id.product_ids:
                self.fsm_order_id.write({
                    'product_ids': [(4, self.product_id.id)]
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
            
    def _create_or_update_sale_order(self):
        """Create or update the sale order"""
        if not self.fsm_order_id.sale_order_id:
            # Get the warehouse and picking type
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            if not warehouse:
                raise ValidationError(_('No warehouse found. Please configure a warehouse first.'))
            
            # Ensure we have a proper picking type ID
            picking_type_id = self.picking_type_id.id if self.picking_type_id else warehouse.out_type_id.id
            
            # Create new sale order with required fields
            sale_order_vals = {
                'partner_id': self.fsm_order_id.location_id.partner_id.id,
                'origin': self.fsm_order_id.name,
                'warehouse_id': warehouse.id,
                'picking_type_id': picking_type_id,
            }
            sale_order = self.env['sale.order'].create(sale_order_vals)
            
            # Link the sale order to the FSM order - ONLY use sale_order_id
            self.fsm_order_id.write({
                'sale_order_id': sale_order.id,
            })
        
        # Add product line to existing sale order
        existing_line = self.env['sale.order.line'].search([
            ('order_id', '=', self.fsm_order_id.sale_order_id.id),
            ('product_id', '=', self.product_id.id)
        ], limit=1)  # Add limit=1 to ensure we get only one record
        
        if existing_line:
            # Update existing line quantity
            existing_line.product_uom_qty += self.quantity
        else:
            # Create new line
            self.env['sale.order.line'].create({
                'order_id': self.fsm_order_id.sale_order_id.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.product_id.list_price,
            })