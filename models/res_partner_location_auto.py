# Copyright (C) 2024 - Your Company
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically create FSM location and remove original contact"""
        
        # First create the partners normally
        partners = super().create(vals_list)
        
        # Then process each partner for auto location creation (in reverse order to avoid issues with deletion)
        partners_to_process = []
        for partner in partners:
            # Only process individual contacts (not companies) and not already FSM locations
            if (not partner.is_company and 
                not partner.fsm_location and 
                not self.env.context.get('creating_fsm_location')):
                partners_to_process.append(partner)
        
        # Process partners for auto-location creation
        for partner in partners_to_process:
            self._auto_create_location_and_replace(partner)
        
        return partners

    def _auto_create_location_and_replace(self, original_partner):
        """
        Convert the existing contact directly into an FSM location using Odoo's built-in method
        """
        try:
            _logger.info(f"Converting contact to FSM location: {original_partner.name}")
            
            # Step 1: Mark the partner as an FSM location type
            original_partner.write({
                'type': 'fsm_location',
                'fsm_location': True
            })
            
            # Step 2: Use Odoo's built-in conversion method
            # This is the same method used when you manually convert a contact to FSM location
            fsm_wizard = self.env['fsm.wizard']
            fsm_wizard.action_convert_location(original_partner)
            
            _logger.info(f"Successfully converted contact to FSM location: {original_partner.name}")
            
        except Exception as e:
            _logger.error(f"Failed to convert contact to FSM location for {original_partner.name}: {str(e)}")
            # If something goes wrong, don't break the contact creation
            pass