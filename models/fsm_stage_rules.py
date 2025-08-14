
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
                    # if record.team_leader_id == current_user:
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
        # if self.worker_id != self.env.user:
        #     raise AccessError(_("فقط العامل المخصص يمكنه تحديد مرحلة 'في الطريق'"))
        stage = self.env.ref('fsm_customization.fsm_stage_on_the_way')
        return self.write({'stage_id': stage.id})

    def action_set_work_in_progress(self):
        """Set order stage to 'Work in Progress'"""
        # if self.team_leader_id == self.env.user:
        if self.person_id == self.env.user:
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
            if not rec.stage_reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_postponed')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})

    def action_set_marketing_followup(self):
        """Set order stage to 'Marketing Follow-up'"""
        for rec in self:
            if not rec.stage_reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_marketing_followup')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})

    def action_set_sales_followup(self):
        """Set order stage to 'Sales Follow-up'"""
        for rec in self:
            if not rec.stage_reason:
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
            if not rec.stage_reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_cancelled')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})
    
    # def action_cancel_order(self):
    #     """Cancel the order"""
    #     for rec in self:
    #         if not rec.stage_reason:
    #             raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
    #         cancelled_stage = self.env.ref('fsm_customization.fsm_stage_cancelled')
    #         rec.stage_id = cancelled_stage
    #     return self.write({'stage_id': cancelled_stage.id})
    
    def action_set_completion_request(self):
        """Set order stage to 'Work Completion Request'"""
        # if self.team_leader_id == self.env.user:
        if self.person_id == self.env.user:
            if self.stage_id.name != 'جاري العمل':
                raise ValidationError(_("التيم ليدر يمكنه اختيار 'طلب اتمام العمل' فقط بعد مرحلة 'جاري العمل'"))
        
        for rec in self:
            if  not rec.type or not rec.operation_type_id:
                raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
            if  not rec.problem_type_id or not rec.problem_solution_id:
                raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
        stage = self.env.ref('fsm_customization.fsm_stage_completion_request')
        return self.write({'stage_id': stage.id})

    
    # def action_set_work_completed(self):
    #     """Set order stage to 'Work Completed'"""
    #     if self.manager_id != self.env.user:
    #         raise AccessError(_("فقط مشرف الصيانة يمكنه تحديد مرحلة 'تم العمل'"))
    #     for rec in self:
    #         if rec.stage_id.name != 'طلب اتمام العمل':
    #             raise ValidationError("لا يمكن الانتقال إلى 'تم العمل' قبل المرور بمرحلة 'طلب اتمام العمل'.")
    #         if   not rec.type or not rec.operation_type_id:
    #             raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
    #         if   not rec.problem_type_id or not rec.problem_solution_id:
    #             raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
    #         # check also for solution and operation_type (see next section)
    #         # completed_stage = self.env.ref('fsm_customization.fsm_stage_work_completed')
    #         # rec.stage_id = completed_stage
    #     stage = self.env.ref('fsm_customization.fsm_stage_work_completed')
    #     vals = {'stage_id': stage.id}
    #     if not self.date_end:
    #         vals['date_end'] = fields.Datetime.now()
    #     return self.write(vals)
    def action_set_work_completed(self):
        """Set order stage to 'Work Completed'"""
        if self.manager_id != self.env.user:
            raise AccessError(_("فقط مشرف الصيانة يمكنه تحديد مرحلة 'تم العمل'"))
        
        # Validate all records before making any changes
        for rec in self:
            if rec.stage_id.name != 'طلب اتمام العمل':
                raise ValidationError("لا يمكن الانتقال إلى 'تم العمل' قبل المرور بمرحلة 'طلب اتمام العمل'.")
            if not rec.type or not rec.operation_type_id:
                raise ValidationError("يرجى إدخال العملية ونوع العملية قبل إتمام العمل.")
            if not rec.problem_type_id or not rec.problem_solution_id:
                raise ValidationError("يرجى إدخال المشكلة والحل قبل إتمام العمل.")
        
        # Prepare values for update
        stage = self.env.ref('fsm_customization.fsm_stage_work_completed')
        vals = {'stage_id': stage.id}
        if not self.date_end:
            vals['date_end'] = fields.Datetime.now()
        
        # Perform the write operation
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
            
            # if  rec.team_leader_id == self.env.user :
            if  rec.person_id == self.env.user :
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
            if not rec.stage_reason:
                raise ValidationError("الرجاء تعبئة حقل السبب قبل الإلغاء.")
            cancelled_stage = self.env.ref('fsm_customization.fsm_stage_emergency_stop')
            rec.stage_id = cancelled_stage
        return self.write({'stage_id': cancelled_stage.id})