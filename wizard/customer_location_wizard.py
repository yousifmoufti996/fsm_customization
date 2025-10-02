# Copyright (C) 2024
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class CustomerLocationWizard(models.TransientModel):
    _name = 'customer.location.wizard'
    _description = 'Get Customer Current Location'
    
    # customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')
    latitude = fields.Float('خط العرض',digits=(23, 20))
    longitude = fields.Float('خط الطول',digits=(23, 20))
    accuracy_m = fields.Float('الدقة (م)', digits=(10, 2))
    
    # Display current coordinates if they exist
    current_latitude = fields.Float(
        string='خط العرض الحالي', 
        related='customer_id.partner_latitude', 
        readonly=True
    )
    current_longitude = fields.Float(
        string='خط الطول الحالي', 
        related='customer_id.partner_longitude', 
        readonly=True
    )
    
    def action_save_customer_location(self):
        """Save the coordinates to customer's partner record"""
        self.ensure_one()
        if self.latitude and self.longitude:
            self.customer_id.write({
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
            })
        # Update FSM order's temporary coordinates if fsm_order_id is provided
        if self.fsm_order_id:
            self.fsm_order_id.write({
                'temp_latitude_coordinates': self.latitude,
                'temp_longitude_coordinates': self.longitude,
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تم بنجاح!',
                    'message': f'تم حفظ موقع العميل: {self.latitude}, {self.longitude}',
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    },
                }
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_get_customer_browser_location(self):
        """Ask the frontend to get the GPS and write back to THIS wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'get_customer_current_location',
            'params': {'wizard_id': self.id},
        }