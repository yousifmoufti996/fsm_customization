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
        
    # def action_create_fsm_ticket(self):
    #     """Action to create a new FSM ticket/order for this partner"""
    #     self.ensure_one()
        
    #     # Check if partner has FSM location, if not create one
    #     fsm_location = self.env['fsm.location'].search([
    #         '|',
    #         ('partner_id', '=', self.id),
    #         ('owner_id', '=', self.id)
    #     ], limit=1)
        
    #     if not fsm_location:
    #         # Create FSM location for this partner
    #         fsm_location = self.env['fsm.location'].create({
    #             'partner_id': self.id,
    #             'owner_id': self.id,
    #             'name': self.name,
    #         })

    #     # Return action to open FSM ticket creation wizard or form
    #     return {
    #         'name': 'Create Field Service Ticket',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'fsm.order',
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_location_id': fsm_location.id,
    #             'default_partner_id': self.id,
    #         }
    #     }

    # def action_view_fsm_tickets(self):
    #     """Action to view all FSM tickets/orders for this partner"""
    #     self.ensure_one()
        
    #     # Get helpdesk tickets
    #     helpdesk_tickets = self.env['helpdesk.ticket'].search([
    #         ('partner_id', '=', self.id)
    #     ])
        
    #     # Get FSM orders
    #     locations = self.env['fsm.location'].search([
    #         '|', 
    #         ('partner_id', '=', self.id),
    #         ('owner_id', '=', self.id)
    #     ])
    #     fsm_orders = self.env['fsm.order'].search([
    #         ('location_id', 'in', locations.ids)
    #     ]) if locations else self.env['fsm.order']
        
    #     # If we have both, show a selection dialog
    #     if helpdesk_tickets and fsm_orders:
    #         return {
    #             'name': 'Choose Ticket Type',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'fsm.ticket.selection.wizard',
    #             'view_mode': 'form',
    #             'target': 'new',
    #             'context': {
    #                 'default_partner_id': self.id,
    #                 'helpdesk_ticket_ids': helpdesk_tickets.ids,
    #                 'fsm_order_ids': fsm_orders.ids,
    #             }
    #         }
    #     elif helpdesk_tickets:
    #         # Show helpdesk tickets
    #         return {
    #             'name': 'Helpdesk Tickets',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'helpdesk.ticket',
    #             'view_mode': 'tree,form',
    #             'domain': [('id', 'in', helpdesk_tickets.ids)],
    #             'context': {'default_partner_id': self.id}
    #         }
    #     elif fsm_orders:
    #         # Show FSM orders
    #         return {
    #             'name': 'Field Service Orders',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'fsm.order',
    #             'view_mode': 'tree,form',
    #             'domain': [('id', 'in', fsm_orders.ids)],
    #         }
    #     else:
    #         # No tickets found, create new one
    #         return self.action_create_fsm_ticket()