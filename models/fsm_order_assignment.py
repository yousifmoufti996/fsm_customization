# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError 


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        tracking=True,
        help='Team leader responsible for this order'
    )
    manager_id = fields.Many2one(
        'res.users', 
        string='Manager',
        tracking=True,
        help='Manager overseeing this order'
    )
    worker_id = fields.Many2one(
        'res.users',
        string='Worker',
        tracking=True,
        help='Worker assigned to execute this order'
    )



    @api.onchange('team_id')
    def _onchange_team_id_assignment(self):
        """Auto-assign team leader when team changes"""
        if self.team_id and hasattr(self.team_id, 'user_id') and self.team_id.user_id:
            self.team_leader_id = self.team_id.user_id


    def action_assign_team_leader(self):
        """Action to assign a team leader"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Team Leader',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('share', '=', False)],
            'target': 'new',
            'context': {
                'default_groups_id': [(4, self.env.ref('base.group_user').id)],
            }
        }

    def action_assign_manager(self):
        """Action to assign a manager"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Manager',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('share', '=', False)],
            'target': 'new',
            'context': {
                'default_groups_id': [(4, self.env.ref('base.group_user').id)],
            }
        }

    def action_assign_worker(self):
        """Action to assign a worker"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Worker',
            'res_model': 'res.users',
            'view_mode': 'tree,form', 
            'domain': [('share', '=', False)],
            'target': 'new',
            'context': {
                'default_groups_id': [(4, self.env.ref('base.group_user').id)],
            }
        }

    def _send_assignment_notification(self, assigned_user, role):
        """Send notification to assigned user"""
        if assigned_user:
            subject = f"FSM Order Assignment - {role}"
            body = f"""
            <p>Dear {assigned_user.name},</p>
            <p>You have been assigned as <strong>{role}</strong> for FSM Order: <strong>{self.name}</strong></p>
            <p><strong>Customer:</strong> {self.customer_id.name if self.customer_id else 'N/A'}</p>
            <p><strong>Location:</strong> {self.location_id.name if self.location_id else 'N/A'}</p>
            <p><strong>Priority:</strong> {dict(self._fields['priority'].selection).get(self.priority, 'N/A')}</p>
            <p><strong>Scheduled Start:</strong> {self.scheduled_date_start or 'Not scheduled'}</p>
            <p>Please check the order details in the system.</p>
            <p>Best regards,<br/>FSM System</p>
            """
            
            self.message_post(
                body=body,
                subject=subject,
                partner_ids=[assigned_user.partner_id.id],
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )

    # Override write method to add assignment tracking
    def write(self, vals):
        """Override write to add assignment tracking"""
        # Store old values for assignment tracking
        old_assignments = {}
        for record in self:
            old_assignments[record.id] = {
                'team_leader_id': record.team_leader_id,
                'manager_id': record.manager_id,
                'worker_id': record.worker_id,
            }
        
        # Call parent write method
        result = super().write(vals)
        
        # Track assignment changes and send notifications
        for record in self:
            old_vals = old_assignments.get(record.id, {})
            
            # Track team leader changes
            if 'team_leader_id' in vals and old_vals.get('team_leader_id') != record.team_leader_id:
                if record.team_leader_id:
                    record._send_assignment_notification(record.team_leader_id, 'Team Leader')
                    record.message_post(
                        body=f'Team Leader assigned: {record.team_leader_id.name}',
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
            
            # Track manager changes  
            if 'manager_id' in vals and old_vals.get('manager_id') != record.manager_id:
                if record.manager_id:
                    record._send_assignment_notification(record.manager_id, 'Manager')
                    record.message_post(
                        body=f'Manager assigned: {record.manager_id.name}',
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
            
            # Track worker changes
            if 'worker_id' in vals and old_vals.get('worker_id') != record.worker_id:
                if record.worker_id:
                    record._send_assignment_notification(record.worker_id, 'Worker')
                    record.message_post(
                        body=f'Worker assigned: {record.worker_id.name}',
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )
        
        return result