from odoo import fields, models, _, api

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    fsm_order_id = fields.Many2one(
        'fsm.order',
        string='FSM Order'
    )
    
    fsm_order_ids = fields.Many2many(
        'fsm.order',
        'fsm_order_product_rel',
        'product_id',
        'fsm_order_id',
        string='FSM Orders'
    )
    
    is_selected_in_fsm = fields.Boolean(
        compute='_compute_is_selected_in_fsm',
        string='Selected in Current FSM Order'
    )

    @api.depends('fsm_order_ids')
    def _compute_is_selected_in_fsm(self):
        fsm_order_id = self.env.context.get('fsm_order_id')
        for product in self:
            if fsm_order_id:
                product.is_selected_in_fsm = fsm_order_id in product.fsm_order_ids.ids
            else:
                product.is_selected_in_fsm = False

    def action_add_to_fsm_order(self):
        """Add product to FSM order"""
        fsm_order_id = self.env.context.get('fsm_order_id')
        if fsm_order_id:
            fsm_order = self.env['fsm.order'].browse(fsm_order_id)
            if self not in fsm_order.product_ids:
                fsm_order.write({'product_ids': [(4, self.id)]})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Product "%s" added to FSM Order') % self.name,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Info'),
                        'message': _('Product "%s" is already in this FSM Order') % self.name,
                        'type': 'info',
                        'sticky': False,
                    }
                }
        return False
    
    def action_remove_from_fsm_order(self):
        """Remove product from FSM order"""
        fsm_order_id = self.env.context.get('fsm_order_id')
        if fsm_order_id:
            fsm_order = self.env['fsm.order'].browse(fsm_order_id)
            if self in fsm_order.product_ids:
                fsm_order.write({'product_ids': [(3, self.id)]})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Product "%s" removed from FSM Order') % self.name,
                        'type': 'success',
                        'sticky': False,
                    }
                }
        return False

    def toggle_fsm_selection(self):
        """Toggle product selection in FSM order"""
        if self.is_selected_in_fsm:
            return self.action_remove_from_fsm_order()
        else:
            return self.action_add_to_fsm_order()
    def action_open_add_product_wizard(self):
        """Open wizard to add product with quantity"""
        return {
            'name': _('Add Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'add.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
                'fsm_order_id': self.env.context.get('fsm_order_id'),
            }
        }