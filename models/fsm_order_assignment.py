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
    
    # Customer availability time for postponed orders (requirement 3)
    customer_availability_time = fields.Datetime(
        string='وقت تواجد العميل',
        help='Required when order is postponed'
    )
    fields_locked = fields.Boolean("الحقول مقفلة", default=False, readonly=True)
    
    # Add reason field for specific stages
    stage_reason = fields.Text(string='السبب', tracking=True)


    @api.constrains('stage_id')
    def _check_stage_transition_rules(self):
        """Validate stage transitions based on business rules"""
        for record in self:
            if record.id:
                # Get original stage from database to compare
                original_record = self.browse(record.id)
                old_stage = original_record._origin.stage_id if hasattr(original_record, '_origin') and original_record._origin else None
                new_stage = record.stage_id
                current_user = self.env.user
                
                if old_stage and old_stage != new_stage:
                    # Rule 1: From "في الطريق" only allow "جاري العمل" or "توقف طارئ"
                    if old_stage.name == 'في الطريق':
                        allowed_stages = ['جاري العمل', 'توقف طارئ']
                        if new_stage.name not in allowed_stages:
                            raise ValidationError(_(
                                "من مرحلة 'في الطريق' يمكن الانتقال فقط إلى 'جاري العمل' أو 'توقف طارئ'"
                            ))
                    
                    # Rule 2: From "جاري العمل" only allow "تم العمل" or "توقف طارئ"
                    if old_stage.name == 'جاري العمل':
                        allowed_stages = ['تم العمل', 'توقف طارئ']
                        if new_stage.name not in allowed_stages:
                            raise ValidationError(_(
                                "من مرحلة 'جاري العمل' يمكن الانتقال فقط إلى 'تم العمل' أو 'توقف طارئ'"
                            ))
                    
                    # Rule 3: When selecting "مؤجل", customer availability time is required
                    if new_stage.name == 'مؤجل' and not record.customer_availability_time:
                        raise ValidationError(_(
                            "يجب تحديد وقت تواجد العميل عند اختيار مرحلة 'مؤجل'"
                        ))
                    
                    # Rule 6: Only maintenance supervisor can set "تم العمل"
                    if new_stage.name == 'تم العمل':
                        if not record.manager_id or record.manager_id != current_user:
                            raise ValidationError(_(
                                "فقط مشرف الصيانة يمكنه اختيار مرحلة 'تم العمل'"
                            ))
                    
                    # Team Leader Rules
                    if record.team_leader_id == current_user:
                        # Team leader can only select "جاري العمل" after "في الطريق" by supervisor
                        if new_stage.name == 'جاري العمل' and old_stage.name != 'في الطريق':
                            raise ValidationError(_(
                                "التيم ليدر يمكنه اختيار 'جاري العمل' فقط بعد أن تكون في مرحلة 'في الطريق' من قبل المشرف"
                            ))
                        
                        # Team leader can select "طلب اتمام العمل" only after "جاري العمل"
                        if new_stage.name == 'طلب اتمام العمل' and old_stage.name != 'جاري العمل':
                            raise ValidationError(_(
                                "التيم ليدر يمكنه اختيار 'طلب اتمام العمل' فقط بعد مرحلة 'جاري العمل'"
                            ))

    # @api.constrains('stage_id')
    # def _check_stage_transition_from_in_the_way(self):
    #     for record in self:
    #         if hasattr(record, '_origin') and record._origin.stage_id:
    #             old_stage = record._origin.stage_id
    #             new_stage = record.stage_id
                
    #             if old_stage and old_stage != new_stage:
    #                 # Check if old stage was "في الطريق"
    #                 if old_stage.name == 'في الطريق' or old_stage.name == 'On The Way':
    #                     # Define allowed next stages for FSM orders
    #                     allowed_stage_names = ['جاري العمل', 'توقف طارئ','Emergency Stop','Work in Progress']
                        
    #                     if new_stage.name not in allowed_stage_names:
    #                         raise ValidationError(_(
    #                             "إذا كان الطلب في الطريق، يمكنك فقط اختيار 'جاري العمل' أو 'توقف طارئ' كمرحلة تالية.\n"
    #                             "If the order is 'In the Way', you can only select 'Work in Progress' or 'Emergency Stop' as the next stage."
    #                         ))


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

    @api.model
    def is_fsm_manager(self):
        return self.env.user.has_group('fieldservice.group_fsm_manager')
    
    # def write(self, vals):
    #     """Override write to implement business rules and field locking"""
        
    #     # Check if we're transitioning TO 'تم العمل' stage
    #     transitioning_to_completed = False
    #     if 'stage_id' in vals:
    #         new_stage = self.env['fsm.stage'].browse(vals['stage_id'])
    #         if new_stage.name == 'تم العمل':
    #             transitioning_to_completed = True
            
    #         # Track stage changes
    #         for order in self:
    #             self._track_stage_change(order, vals['stage_id'])
        
    #     # Apply business rules for each record
    #     for record in self:
    #         # Rule 4: Lock all fields when work is already completed 
    #         # (except when transitioning TO completed stage)
    #         if record.stage_id.name == 'تم العمل' and not transitioning_to_completed:
    #             # Allow only stage changes by authorized users (if needed)
    #             restricted_fields = set(vals.keys()) - {'stage_id', 'fields_locked'}
    #             print('restricted_fields')
    #             print(restricted_fields)
    #             if restricted_fields:
    #                 raise ValidationError(_(
    #                     "لا يمكن التعديل على الحقول بعد إتمام العمل. الحقول المحظورة: %s"
    #                 ) % ', '.join(restricted_fields))
            
    #         # Rule 5: Manager cannot edit manager assignment for himself
    #         if 'manager_id' in vals and record.manager_id == self.env.user and not self.is_fsm_manager:
    #             if vals['manager_id'] != record.manager_id.id:
    #                 raise ValidationError(_(
    #                     "لا يمكن للمشرف تعديل أو إلغاء حقل إسناد المشرف لنفسه"
    #                 ))
        
    #     # Perform the actual write operation
    #     result = super().write(vals)
        
    #     # Lock fields when work is completed
    #     if 'stage_id' in vals:
    #         new_stage = self.env['fsm.stage'].browse(vals['stage_id'])
    #         for record in self:
    #             if new_stage.name == 'تم العمل':
    #                 record.sudo().write({'fields_locked': True})
        
    #     return result
  