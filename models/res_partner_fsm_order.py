from odoo import api, fields, models, _



class ResPartner(models.Model):
    _inherit = "res.partner"

    # Add field to count FSM tickets/orders
    fsm_ticket_count = fields.Integer(
        string="FSM Tickets",
        compute="_compute_fsm_ticket_count"
    )
    

    
    def action_create_fsm_order(self):
        """Create a new FSM order for this partner"""
        self.ensure_one()
        
        # Check if partner has FSM location, if not create one
        fsm_location = self.env['fsm.location'].search([
            ('partner_id', '=', self.id)
        ], limit=1)
        
        if not fsm_location:
            # Create FSM location for this partner
            fsm_location = self.env['fsm.location'].create({
                'partner_id': self.id,
                'owner_id': self.id,
                'customer_id': self.id,
            })

        # Open FSM order creation form
        return {
            'name': 'Create Field Service Order',
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_location_id': fsm_location.id,
            }
        }
    @api.depends()
    def _compute_fsm_ticket_count(self):
        """Compute the number of FSM tickets/orders for this partner"""
        for partner in self:
            # Count helpdesk tickets related to this partner
            helpdesk_count = self.env['helpdesk.ticket'].search_count([
                ('partner_id', '=', partner.id)
            ])
            
            # Count FSM orders related to this partner's locations
            fsm_order_count = 0
            if hasattr(self.env, 'fsm.order'):
                # If partner has FSM locations, count orders for those locations
                locations = self.env['fsm.location'].search([
                    '|', 
                    ('partner_id', '=', partner.id),
                    ('owner_id', '=', partner.id)
                ])
                if locations:
                    fsm_order_count = self.env['fsm.order'].search_count([
                        ('location_id', 'in', locations.ids)
                    ])
            
            partner.fsm_ticket_count = helpdesk_count + fsm_order_count
        
    