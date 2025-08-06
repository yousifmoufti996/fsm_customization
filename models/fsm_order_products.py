from odoo import _, api, fields, models

class FSMOrder(models.Model):
    _inherit = "fsm.order"
    
    # Add these fields to track products
    product_ids = fields.Many2many(
        'product.product',
        'fsm_order_product_rel',
        'fsm_order_id',
        'product_id',
        string='Products'
    )
    
    product_count = fields.Integer(
        compute="_compute_product_count",
        string="Products Count"
    )
    
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Orders')

    
    @api.depends('product_ids')
    def _compute_product_count(self):
        for order in self:
            order.product_count = len(order.product_ids)
    
    def action_open_products(self):
        """Open products selection view"""
        return {
            'name': _("Choose Products"),
            'view_mode': 'kanban,tree,form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_fsm_order_id': self.id,
                'fsm_order_id': self.id,
                'create': True,
                'edit': True,
            },
            'domain': [],
            'views': [
                [False, 'kanban'],
                [False, 'list'],
                [False, 'form']
            ]
        }
        
    @api.depends('sale_order_id')
    def _compute_sale_order_count(self):
        for order in self:
            order.sale_order_count = 1 if order.sale_order_id else 0

    def action_create_sale_order(self):
        """Create sale order from FSM order products"""
        if not self.product_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('Please add products first before creating sale order.'),
                    'type': 'warning',
                }
            }
        
        if self.sale_order_id:
            # If sale order already exists, just open it
            return self.action_view_sale_order()
        
        # Create new sale order
        sale_order_vals = {
            'partner_id': self.location_id.partner_id.id,
            'origin': self.name,
            'order_line': [],
        }
        
        # Add order lines for each product
        for product in self.product_ids:
            line_vals = {
                'product_id': product.id,
                'product_uom_qty': 1.0,  # Default quantity, will be enhanced later
                'price_unit': product.list_price,
            }
            sale_order_vals['order_line'].append((0, 0, line_vals))
        
        # Create the sale order
        sale_order = self.env['sale.order'].create(sale_order_vals)
        self.sale_order_id = sale_order.id
        
        return self.action_view_sale_order()

    def action_view_sale_order(self):
        """Open the related sale order"""
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }