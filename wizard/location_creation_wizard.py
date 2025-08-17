# Copyright (C) 2024 - Your Company
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LocationCreationWizard(models.TransientModel):
    _name = 'location.creation.wizard'
    _description = 'Location Creation Wizard'

    partner_ids = fields.Many2many(
        'res.partner',
        string='Contacts',
        required=True,
        help="Contacts for which to create FSM locations"
    )
    
    remove_parent_contacts = fields.Boolean(
        string='Remove Parent Contacts',
        default=True,
        help="Remove parent contacts after creating locations"
    )
    
    force_creation = fields.Boolean(
        string='Force Creation',
        default=False,
        help="Force creation even if some validations fail"
    )
    
    preview_mode = fields.Boolean(
        string='Preview Mode',
        default=True,
        help="Preview what will be created without actually creating"
    )
    
    line_ids = fields.One2many(
        'location.creation.wizard.line',
        'wizard_id',
        string='Creation Lines',
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        """Set default partner_ids from context"""
        res = super().default_get(fields_list)
        
        if 'partner_ids' in fields_list:
            partner_ids = self.env.context.get('active_ids', [])
            if partner_ids:
                res['partner_ids'] = [(6, 0, partner_ids)]
        
        return res

    @api.onchange('partner_ids', 'preview_mode')
    def _onchange_partners_preview(self):
        """Generate preview lines when partners change"""
        if self.preview_mode and self.partner_ids:
            self._generate_preview_lines()

    def _generate_preview_lines(self):
        """Generate preview lines for selected partners"""
        lines = []
        
        for partner in self.partner_ids:
            status = 'ready'
            message = 'Ready for location creation'
            parent_name = ''
            
            # Validate partner
            if partner.service_location_id:
                status = 'skip'
                message = 'Already has service location'
            elif partner.fsm_location:
                status = 'skip'
                message = 'Is already an FSM location'
            elif not partner.name:
                status = 'error'
                message = 'Partner has no name'
            
            # Check parent
            if partner.parent_id and self.remove_parent_contacts:
                parent_name = partner.parent_id.name
                if partner.parent_id.fsm_location:
                    message += ' (Parent is FSM location - will not be removed)'
            
            lines.append((0, 0, {
                'partner_id': partner.id,
                'partner_name': partner.name,
                'parent_name': parent_name,
                'status': status,
                'message': message,
            }))
        
        self.line_ids = lines

    def action_create_locations(self):
        """Execute the location creation process"""
        if self.preview_mode:
            # Switch to execution mode
            self.preview_mode = False
            self._generate_preview_lines()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'location.creation.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }
        
        # Execute creation
        return self._execute_creation()

    def _execute_creation(self):
        """Execute the actual location creation"""
        partners_to_process = self.partner_ids.filtered(
            lambda p: not p.service_location_id and not p.fsm_location
        )
        
        if not partners_to_process:
            raise UserError(_("No valid partners to process"))
        
        success_count = 0
        failed_partners = []
        
        for partner in partners_to_process:
            try:
                # Create location
                vals = {
                    'auto_create_location': True,
                    'parent_to_remove_id': partner.parent_id.id if (
                        self.remove_parent_contacts and partner.parent_id
                    ) else False
                }
                
                partner_obj = self.env['res.partner']
                partner_obj._auto_create_location_and_remove_parent(partner, vals)
                
                partner.location_creation_status = 'created'
                success_count += 1
                
                # Update line status
                line = self.line_ids.filtered(lambda l: l.partner_id == partner)
                if line:
                    line.status = 'success'
                    line.message = 'Location created successfully'
                
            except Exception as e:
                error_msg = str(e)
                failed_partners.append(f"{partner.name}: {error_msg}")
                partner.location_creation_status = 'failed'
                
                # Update line status
                line = self.line_ids.filtered(lambda l: l.partner_id == partner)
                if line:
                    line.status = 'error'
                    line.message = f'Failed: {error_msg}'
                
                _logger.error(f"Failed to create location for {partner.name}: {error_msg}")
        
        # Update preview lines to show results
        self._generate_result_message(success_count, failed_partners)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'location.creation.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def _generate_result_message(self, success_count, failed_partners):
        """Generate result message and notification"""
        message = f"Successfully created {success_count} locations."
        
        if failed_partners:
            message += f"\nFailed: {len(failed_partners)} contacts"
            if len(failed_partners) <= 5:
                message += "\n" + "\n".join(failed_partners)
            else:
                message += "\n" + "\n".join(failed_partners[:5])
                message += f"\n... and {len(failed_partners) - 5} more"
        
        notification_type = 'success' if not failed_partners else 'warning'
        
        # Store message for display
        self.env['ir.config_parameter'].sudo().set_param(
            f'location_creation_result_{self.id}', 
            message
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Location Creation Complete'),
                'message': message,
                'type': notification_type,
            }
        }


class LocationCreationWizardLine(models.TransientModel):
    _name = 'location.creation.wizard.line'
    _description = 'Location Creation Wizard Line'

    wizard_id = fields.Many2one(
        'location.creation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True
    )
    
    partner_name = fields.Char(
        string='Contact Name',
        readonly=True
    )
    
    parent_name = fields.Char(
        string='Parent Contact',
        readonly=True
    )
    
    status = fields.Selection([
        ('ready', 'Ready'),
        ('skip', 'Skip'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Status', default='ready')
    
    message = fields.Text(
        string='Message',
        readonly=True
    )