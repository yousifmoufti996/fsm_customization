
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class FSMOrder(models.Model):
    _inherit = 'fsm.order'
# Lock fields when work is completed
    fields_locked = fields.Boolean("الحقول مقفلة", default=False, readonly=True)
    is_on_the_way = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_work_in_progress = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_postponed = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_marketing_followup = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_sales_followup = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_waiting = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_cancelled = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_completion_request = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_work_completed = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_audited = fields.Boolean(compute='_compute_stage_flags', store=False)
    is_emergency_stop = fields.Boolean(compute='_compute_stage_flags', store=False)

    @api.constrains('stage_id')
    def _check_stage_transition_rules(self):
        """Validate stage transitions based on business rules"""
        for record in self:
            # Get the original stage from the database
            if record.id:
                original_record = self.env['fsm.order'].browse(record.id)
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
                    
                    # Rule 2: From "جاري العمل" only allow "طلب اتمام العمل" or "توقف طارئ"
                    if old_stage.name == 'جاري العمل':
                        allowed_stages = ['طلب اتمام العمل', 'توقف طارئ']
                        if new_stage.name not in allowed_stages:
                            raise ValidationError(_(
                                "من مرحلة 'جاري العمل' يمكن الانتقال فقط إلى 'طلب اتمام العمل' أو 'توقف طارئ'"
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
    # def write(self, vals):
    #     """Override write to implement business rules and field locking"""
    #     original_stages = {}
    #     for record in self:
    #         # Rule 4: Lock all fields when work is completed (except for manager)
    #         if record.stage_id.name == 'تم العمل' and record.manager_id != self.env.user:
    #             # Allow only stage changes by authorized users
    #             restricted_fields = set(vals.keys()) - {'stage_id', 'fields_locked'}
    #             if restricted_fields:
    #                 raise ValidationError(_(
    #                     "لا يمكن التعديل على الحقول بعد إتمام العمل. الحقول المحظورة: %s"
    #                 ) % ', '.join(restricted_fields))
            
    #         # Rule 5: Manager cannot edit manager assignment for himself
    #         if 'manager_id' in vals and record.manager_id == self.env.user:
    #             if vals['manager_id'] != record.manager_id.id:
    #                 raise ValidationError(_(
    #                     "لا يمكن للمشرف تعديل أو إلغاء حقل إسناد المشرف لنفسه"
    #                 ))
            
    #         # Prevent team leader from editing start times
    #         if record.team_leader_id == self.env.user:
    #             time_fields = [
    #                 'on_the_way_start_time', 'work_in_progress_start_time',
    #                 'postponed_start_time', 'marketing_followup_start_time',
    #                 'sales_followup_start_time', 'waiting_start_time',
    #                 'completion_request_start_time', 'work_completed_start_time',
    #                 'audited_start_time', 'emergency_stop_start_time'
    #             ]
    #             restricted_time_fields = set(vals.keys()) & set(time_fields)
    #             if restricted_time_fields:
    #                 raise ValidationError(_(
    #                     "التيم ليدر لا يمكنه التعديل على أوقات البدء"
    #                 ))
                    
    #     # Validate stage transitions before writing
    #     if 'stage_id' in vals:
    #         new_stage_id = vals['stage_id']
    #         new_stage = self.env['fsm.stage'].browse(new_stage_id)
    #         current_user = self.env.user
            
    #         for record in self:
    #             old_stage = original_stages.get(record.id)
                
    #             if old_stage and old_stage != new_stage:
    #                 # Rule 1: From "في الطريق" only allow "جاري العمل" or "توقف طارئ"
    #                 if old_stage.name == 'في الطريق':
    #                     allowed_stages = ['جاري العمل', 'توقف طارئ']
    #                     if new_stage.name not in allowed_stages:
    #                         raise ValidationError(_(
    #                             "من مرحلة 'في الطريق' يمكن الانتقال فقط إلى 'جاري العمل' أو 'توقف طارئ'"
    #                         ))
                    
    #                 # Rule 2: From "جاري العمل" only allow "طلب اتمام العمل" or "توقف طارئ"
    #                 if old_stage.name == 'جاري العمل':
    #                     allowed_stages = ['طلب اتمام العمل', 'توقف طارئ']
    #                     if new_stage.name not in allowed_stages:
    #                         raise ValidationError(_(
    #                             "من مرحلة 'جاري العمل' يمكن الانتقال فقط إلى 'طلب اتمام العمل' أو 'توقف طارئ'"
    #                         ))
                    
    #                 # Rule 3: When selecting "مؤجل", customer availability time is required
    #                 if new_stage.name == 'مؤجل' and not record.customer_availability_time and 'customer_availability_time' not in vals:
    #                     raise ValidationError(_(
    #                         "يجب تحديد وقت تواجد العميل عند اختيار مرحلة 'مؤجل'"
    #                     ))
                    
    #                 # Rule 6: Only maintenance supervisor can set "تم العمل"
    #                 if new_stage.name == 'تم العمل':
    #                     if not record.manager_id or record.manager_id != current_user:
    #                         raise ValidationError(_(
    #                             "فقط مشرف الصيانة يمكنه اختيار مرحلة 'تم العمل'"
    #                         ))
                    
    #                 # Team Leader Rules
    #                 if record.team_leader_id == current_user:
    #                     # Team leader can only select "جاري العمل" after "في الطريق" by supervisor
    #                     if new_stage.name == 'جاري العمل' and old_stage.name != 'في الطريق':
    #                         raise ValidationError(_(
    #                             "التيم ليدر يمكنه اختيار 'جاري العمل' فقط بعد أن تكون في مرحلة 'في الطريق' من قبل المشرف"
    #                         ))
                        
    #                     # Team leader can select "طلب اتمام العمل" only after "جاري العمل"
    #                     if new_stage.name == 'طلب اتمام العمل' and old_stage.name != 'جاري العمل':
    #                         raise ValidationError(_(
    #                             "التيم ليدر يمكنه اختيار 'طلب اتمام العمل' فقط بعد مرحلة 'جاري العمل'"
    #                         ))
        
    #     result = super().write(vals)
    #     # Update start times when stage changes
    #     if 'stage_id' in vals:
    #         new_stage = self.env['fsm.stage'].browse(vals['stage_id'])
    #         current_time = fields.Datetime.now()
            
    #         for record in self:
    #             # Set start time for each stage
    #             stage_time_mapping = {
    #                 'في الطريق': 'on_the_way_start_time',
    #                 'جاري العمل': 'work_in_progress_start_time',
    #                 'مؤجل': 'postponed_start_time',
    #                 'متابعة التسويق': 'marketing_followup_start_time',
    #                 'متابعة المبيعات': 'sales_followup_start_time',
    #                 'في الانتظار': 'waiting_start_time',
    #                 'طلب اتمام العمل': 'completion_request_start_time',
    #                 'تم العمل': 'work_completed_start_time',
    #                 'تم التدقيق': 'audited_start_time',
    #                 'توقف طارئ': 'emergency_stop_start_time'
    #             }
                
    #             if new_stage.name in stage_time_mapping:
    #                 time_field = stage_time_mapping[new_stage.name]
    #                 if not getattr(record, time_field):
    #                     # Use sudo to bypass readonly constraints when setting timestamps
    #                     record.sudo().write({time_field: current_time})
                
    #             # Lock fields when work is completed
    #             if new_stage.name == 'تم العمل':
    #                 record.sudo().write({'fields_locked': True})
        
    #     return result
    def _compute_stage_flags(self):
        stage_refs = {
            'is_on_the_way': 'fsm_customization.fsm_stage_on_the_way',
            'is_work_in_progress': 'fsm_customization.fsm_stage_work_in_progress',
            'is_postponed': 'fsm_customization.fsm_stage_postponed',
            'is_marketing_followup': 'fsm_customization.fsm_stage_marketing_followup',
            'is_sales_followup': 'fsm_customization.fsm_stage_sales_followup',
            'is_waiting': 'fsm_customization.fsm_stage_waiting',
            'is_cancelled': 'fsm_customization.fsm_stage_cancelled',
            'is_completion_request': 'fsm_customization.fsm_stage_completion_request',
            'is_work_completed': 'fsm_customization.fsm_stage_work_completed',
            'is_audited': 'fsm_customization.fsm_stage_audited',
            'is_emergency_stop': 'fsm_customization.fsm_stage_emergency_stop',
        }
        # Cache stage_ids only once for performance
        resolved_ids = {}
        for key, xml_id in stage_refs.items():
            try:
                resolved_ids[key] = self.env.ref(xml_id).id
            except ValueError:
                resolved_ids[key] = False

        for rec in self:
            for key in stage_refs:
                setattr(rec, key, rec.stage_id.id == resolved_ids[key])
            
            
    
    def action_set_on_the_way(self):
        """Set order stage to 'On The Way'"""
        if self.worker_id != self.env.user:
            raise AccessError(_("فقط العامل المخصص يمكنه تحديد مرحلة 'في الطريق'"))
        stage = self.env.ref('fsm_customization.fsm_stage_on_the_way')
        return self.write({'stage_id': stage.id})

    def action_set_work_in_progress(self):
        """Set order stage to 'Work in Progress'"""
        if self.team_leader_id == self.env.user:
            if self.stage_id.name != 'في الطريق':
                raise ValidationError(_("التيم ليدر يمكنه اختيار 'جاري العمل' فقط بعد مرحلة 'في الطريق'"))
        
        stage = self.env.ref('fsm_customization.fsm_stage_work_in_progress')
        vals = {'stage_id': stage.id}
        if not self.date_start:
            vals['date_start'] = fields.Datetime.now()
        return self.write(vals)

    def action_set_postponed(self):
        """Set order stage to 'Postponed'"""
        if not self.customer_availability_time:
            raise ValidationError(_("يجب تحديد وقت تواجد العميل عند اختيار مرحلة 'مؤجل'"))
        for rec in self:
            if not rec.reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_postponed')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})

    def action_set_marketing_followup(self):
        """Set order stage to 'Marketing Follow-up'"""
        for rec in self:
            if not rec.reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_marketing_followup')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})

    def action_set_sales_followup(self):
        """Set order stage to 'Sales Follow-up'"""
        for rec in self:
            if not rec.reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_sales_followup')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})

    def action_set_waiting(self):
        """Set order stage to 'Waiting'"""
        stage = self.env.ref('fsm_customization.fsm_stage_waiting')
        return self.write({'stage_id': stage.id})

    def action_set_cancelled(self):
        for rec in self:
            if not rec.reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_cancelled')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})
    
    # def action_cancel_order(self):
    #     """Cancel the order"""
    #     for rec in self:
    #         if not rec.reason:
    #             raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
    #         cancelled_stage = self.env.ref('fsm_customization.fsm_stage_cancelled')
    #         rec.stage_id = cancelled_stage
    #     return self.write({'stage_id': cancelled_stage.id})
    
    def action_set_completion_request(self):
        """Set order stage to 'Work Completion Request'"""
        if self.team_leader_id == self.env.user:
            if self.stage_id.name != 'جاري العمل':
                raise ValidationError(_("التيم ليدر يمكنه اختيار 'طلب اتمام العمل' فقط بعد مرحلة 'جاري العمل'"))
        
        for rec in self:
            if  not rec.type or not rec.operation_type_id:
                raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
            if  not rec.problem_type_id or not rec.problem_solution_id:
                raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
        stage = self.env.ref('fsm_customization.fsm_stage_completion_request')
        return self.write({'stage_id': stage.id})

    def action_set_work_completed(self):
        """Set order stage to 'Work Completed'"""
        if self.manager_id != self.env.user:
            raise AccessError(_("فقط مشرف الصيانة يمكنه تحديد مرحلة 'تم العمل'"))
        for rec in self:
            if rec.stage_id.name != 'طلب اتمام العمل':
                raise ValidationError("لا يمكن الانتقال إلى 'تم العمل' قبل المرور بمرحلة 'طلب اتمام العمل'.")
            if   not rec.type or not rec.operation_type_id:
                raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
            if   not rec.problem_type_id or not rec.problem_solution_id:
                raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
            # check also for solution and operation_type (see next section)
            completed_stage = self.env.ref('fsm_customization.fsm_stage_work_completed')
            rec.stage_id = completed_stage
        stage = self.env.ref('fsm_customization.fsm_stage_work_completed')
        vals = {'stage_id': stage.id}
        if not self.date_end:
            vals['date_end'] = fields.Datetime.now()
        return self.write(vals)
    

    def action_set_audited(self):
        """Set order stage to 'Audited'"""
        for rec in self:
            
            if rec.stage_id.name != 'تم العمل':
                
                raise ValidationError("لا يمكن الانتقال إلى 'تم التدقيق' قبل المرور بمرحلة 'تم العمل'.")
            if  not rec.type or not rec.operation_type_id:
                raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
            if  not rec.problem_type_id or not rec.problem_solution_id:
                raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
            
            if  rec.team_leader_id == self.env.user :
                # (record.manager_id == self.env.user and self.env.user != record.person_id)
                raise ValidationError("ليست صلاحيات التيم ليدر")
            audited_stage = self.env.ref('fsm_customization.fsm_stage_audited')
            rec.stage_id = audited_stage
        stage = self.env.ref('fsm_customization.fsm_stage_audited')
        return self.write({'stage_id': stage.id})

    def action_set_emergency_stop(self):
        """Set order stage to 'Emergency Stop'"""
        # stage = self.env.ref('fsm_customization.fsm_stage_emergency_stop')
        # return self.write({'stage_id': stage.id})
        for rec in self:
            if not rec.reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_emergency_stop')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})