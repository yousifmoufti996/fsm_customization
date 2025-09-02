# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError 


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    team_leader_id = fields.Many2one(
        'res.partner',
        string='Team Leader',
        tracking=True,
        help='Team leader responsible for this order'
    )
    manager_id = fields.Many2one(
        'hr.employee',  
        string='Supervisor',
        tracking=True,
        ondelete='set null',
        help='Manager overseeing this order'
    )
    worker_id = fields.Many2one(
        'hr.employee',  # Changed from 'res.partner'
        string='Worker',
        tracking=True,
        ondelete='set null',
        help='Worker assigned to execute this order'
    )

    # Change auditor_id third
    auditor_id = fields.Many2one(
        'hr.employee',  # Changed from 'res.users'
        string='Auditor',
        domain="[('user_id.groups_id.name', 'in', ['Auditor User', 'Access Rights', 'Settings'])]",
        tracking=True,
        ondelete='set null',
        default=lambda self: self._get_default_auditor(),
        help='المستخدم المسؤول عن تدقيق الطلب'
    )
    def _get_default_auditor(self):
        """Get default auditor based on business rules - updated for hr.employee"""
        # Find employee with auditor role
        auditor_users = self.env['res.users'].search([
            ('groups_id.name', 'in', ['Auditor User', 'Access Rights', 'Settings'])
        ], limit=1)
        
        if auditor_users:
            # Find employee linked to this user
            employee = self.env['hr.employee'].search([
                ('user_id', '=', auditor_users.id)
            ], limit=1)
            if employee:
                return employee.id
        return False
    
    # def _get_default_auditor(self):
    #     """Get default auditor based on business rules"""
    
    #     # Option 2: First user with auditor role
    #     auditor_group = self.env.ref('your_module.group_fsm_auditor', raise_if_not_found=False)
    #     if auditor_group:
    #         auditor_users = self.env['res.users'].search([('groups_id', 'in', auditor_group.id)], limit=1)
    #         if auditor_users:
    #             return auditor_users.id

        
     
    # Customer availability time for postponed orders (requirement 3)
    customer_availability_time = fields.Datetime(
        string='وقت تواجد العميل',
        help='Required when order is postponed'
    )
    
    @api.onchange('customer_availability_time')
    def _onchange_customer_availability_time2(self):
        """Warn user if selecting past time"""
        if self.customer_availability_time:
            if self.customer_availability_time <= fields.Datetime.now():
                return {
                    'warning': {
                        'title': 'تحذير',
                        'message': 'وقت تواجد العميل يجب أن يكون في المستقبل'
                    }
                }
  
    fields_locked = fields.Boolean("الحقول مقفلة", default=False, readonly=True)
    

    @api.constrains('stage_id')
    def _check_stage_transition_rules(self):
        """Validate stage transitions based on business rules"""
        is_super_admin = self.env.user.has_group('base.group_system')
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
                        if not is_super_admin and (not record.manager_id or record.manager_id.user_id != current_user):
                            raise ValidationError(_(
                                "فقط مشرف الصيانة يمكنه اختيار مرحلة 'تم العمل'"
                            ))
                    
                    # Team Leader Rules
                    if record.person_id == current_user:
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

   

    @api.onchange('team_id')
    def _onchange_team_id_assignment(self):
        """Auto-assign team leader when team changes"""
        if self.team_id and hasattr(self.team_id, 'user_id') and self.team_id.user_id:
            # self.team_leader_id = self.team_id.user_id
            self.person_id = self.team_id.user_id


    def action_assign_team_leader(self):
        """Action to assign a team leader"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Team Leader',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
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
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'target': 'new',
            'domain': [('user_id', '!=', False)],
            'context': {}
        }

    def action_assign_worker(self):
        """Action to assign a worker"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Worker',
            'res_model': 'res.users',
            'view_mode': 'tree,form', 
            'target': 'new',
            'context': {
                'default_groups_id': [(4, self.env.ref('base.group_user').id)],
            }
        }

  
    @api.model
    def is_fsm_manager(self):
        return self.env.user.has_group('fieldservice.group_fsm_manager')
    
   