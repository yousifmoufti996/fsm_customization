# models/current_location_wizard.py
from odoo import fields, models, api

class CurrentLocationWizard(models.TransientModel):
    _name = 'current.location.wizard'
    _description = 'Get Current Location'
    
    partner_id = fields.Many2one('res.partner', required=True)
    latitude = fields.Float('Latitude',digits=(23, 20))
    longitude = fields.Float('Longitude',digits=(23, 20))
    accuracy_m = fields.Float('Accuracy (m)', digits=(10, 2))
    
    def action_save_location(self):
        self.ensure_one()
        if self.latitude and self.longitude:
            self.partner_id.write({
                'partner_latitude': self.latitude,
                'partner_longitude': self.longitude,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'تم بنجاح!',
                    'message': f'تم حفظ الموقع: {self.latitude}, {self.longitude}',
                    'type': 'success',
                    'sticky': False,  # toast auto-hides
                    'next': {         # <-- close the dialog after the toast
                        'type': 'ir.actions.act_window_close'
                    },
                }
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_get_browser_location(self):
        """Ask the frontend to get the GPS and write back to THIS wizard."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'get_current_location',   # <== Our custom client action
           
            'params': {'wizard_id': self.id},
        }

   
