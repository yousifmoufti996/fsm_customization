# fsm_order_dashboard.py
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from collections import defaultdict


class FSMOrderDashboard(models.TransientModel):
    _name = "fsm.order.dashboard"
    _description = "FSM Order Dashboard"
    _rec_name = "name"
    _transient_max_hours = 0.5
    _transient_max_count = 2

    
    name = fields.Char(
        string="اسم الداشبورد",
        default="داشبورد العمليات",
        required=True
    )
    # فلاتر التاريخ
    date_from = fields.Date(
        string="من تاريخ", 
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )
    date_to = fields.Date(
        string="إلى تاريخ", 
        default=fields.Date.today
    )
    
    # فلاتر إضافية
    team_id = fields.Many2one('fsm.team', string="الفريق")
    person_id = fields.Many2one('fsm.person', string="الموظف")
    
    # إحصائيات العمليات
    completed_orders_count = fields.Integer(
        string="العمليات المكتملة",
        compute="_compute_order_statistics"
    )
    cancelled_orders_count = fields.Integer(
        string="العمليات الملغية", 
        compute="_compute_order_statistics"
    )
    in_progress_orders_count = fields.Integer(
        string="العمليات جاري العمل",
        compute="_compute_order_statistics"
    )
    postponed_orders_count = fields.Integer(
        string="العمليات مؤجلة",
        compute="_compute_order_statistics"
    )
    
    # إحصائيات التكرار
    duplicate_customer_orders_count = fields.Integer(
        string="العمليات المكررة لنفس العميل",
        compute="_compute_duplicate_statistics"
    )
    duplicate_vat_orders_count = fields.Integer(
        string="العمليات المكررة لنفس العامود فات",
        compute="_compute_duplicate_statistics"
    )
    
    # إحصائيات الوقت
    unsolved_12h_orders_count = fields.Integer(
        string="العمليات التي لم يتم حلها بعد 12 ساعة",
        compute="_compute_time_statistics"
    )
    
    # إحصائيات الموظفين
    employee_order_countss = fields.Html(
        string="عدد العمليات لكل موظف",
        compute="_compute_employee_statisticss"
    )
    
    sla_violated_orders_count = fields.Integer(
        string="عدد عمليات SLA",
        compute="_compute_order_statistics"
    )
    
    @api.depends('date_from', 'date_to', 'team_id')
    def _compute_employee_statisticss(self):
        for record in self:
            try:
                domain = record._get_base_domain()
                domain = [d for d in domain if not (isinstance(d, tuple) and d[0] == 'person_id')]
                print('11__name__')

                all_orders = self.env['fsm.order'].search(domain)
                employee_counts = defaultdict(int)
                print('2222__name__')

                for order in all_orders:
                    print('for')
                    if order.person_id:
                        print('if')
                        employee_counts[order.person_id.name] += 1
                    else:
                        print('else')
                        employee_counts['غير محدد'] += 1

                print('if employee_counts:')
                if employee_counts:
                    print('in if employee_counts:')
                    table_rows = ''.join(
                        f"<tr><td>{employee}</td><td>{count} عملية</td></tr>"
                        for employee, count in sorted(employee_counts.items(), key=lambda x: x[1], reverse=True)
                    )
                    print('table row')
                    html = f"""
                        <table class='table table-bordered table-striped' 
                            style="width: 100%; direction: rtl; text-align: right; font-size: 15px; border: 1px solid #ccc;">
                            <thead>
                                <tr style="background-color: #875A7B; color: white;">
                                    <th style="padding: 15px; font-size: 25px;">اسم الموظف</th>
                                    <th style="padding: 15px; font-size: 25px;">عدد العمليات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_rows}
                            </tbody>
                        </table>
                    """
                else:
                    print('else employee_counts')
                    html = "<p>لا توجد عمليات</p>"

                record.employee_order_countss = html
            except Exception as e:
                # Fallback to safe default and optionally log error
                record.employee_order_countss = "<p>حدث خطأ أثناء حساب الإحصائيات</p>"
               
    # إجمالي العمليات
    total_orders_count = fields.Integer(
        string="إجمالي العمليات",
        compute="_compute_order_statistics"
    )

    def _get_base_domain(self):
        """إنشاء domain أساسي للفلترة"""
        domain = []
        
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.team_id:
            domain.append(('team_id', '=', self.team_id.id))
        if self.person_id:
            domain.append(('person_id', '=', self.person_id.id))
            
        return domain

    @api.depends('date_from', 'date_to', 'team_id', 'person_id')
    def _compute_order_statistics(self):
        for record in self:
            domain = record._get_base_domain()
            all_orders = self.env['fsm.order'].search(domain)
            
            # إجمالي العمليات
            record.total_orders_count = len(all_orders)
            
            # العمليات المكتملة - البحث عن stage مكتملة
            # completed_orders = all_orders.filtered(lambda o: 'Work Completed' in o.stage_id.name.lower() or 'Completed' in o.stage_id.name.lower() or 'completed' in o.stage_id.name.lower() or 'work completed' in o.stage_id.name.lower())
            # completed_orders = all_orders.filtered(lambda o:'work completed' in o.stage_id.name.lower() or 'تم العمل' in o.stage_id.name)
            # completed_orders = all_orders.filtered(lambda o: 'work completed' in o.stage_id.name or 'تم العمل' in o.stage_id.name)
            completed_orders = all_orders.filtered(lambda o: o.stage_id.name and ('Work Completed' in o.stage_id.name.lower() or 'Completed' in o.stage_id.name.lower() or 'completed' in o.stage_id.name.lower() or 'work completed' in o.stage_id.name.lower()))

            record.completed_orders_count = len(completed_orders)
            
            # العمليات الملغية - البحث عن stage ملغية
            cancelled_orders = all_orders.filtered(lambda o:o.stage_id.name and ('cancel' in o.stage_id.name.lower() or 'ملغي' in o.stage_id.name or 'Cancelled' in o.stage_id.name))
            record.cancelled_orders_count = len(cancelled_orders)
            
            
            
            # جاري العمل -
            Progress_orders = all_orders.filtered(lambda o:o.stage_id.name and ( 'Work in Progress' in o.stage_id.name.lower() or 'work in progress' in o.stage_id.name.lower() or  'جاري العمل' in o.stage_id.name))
            record.in_progress_orders_count = len(Progress_orders)
            
            
            # العمليات المؤجلة
            Postponed_orders = all_orders.filtered(lambda o:o.stage_id.name and ( 'Postponed' in o.stage_id.name.lower() or 'postponed' in o.stage_id.name.lower() or 'المؤجلة' in o.stage_id.name or 'مؤجل' in o.stage_id.name))
            record.postponed_orders_count = len(Postponed_orders)
        
            
            for order in all_orders:
                print("Order:", order.name)
                print("Duration:", order.creation_to_work_done_duration)
                print("Estimated:", order.estimated_problem_duration)
                print('sla_violated_orders')
            
            print('record.work_progress_to_done_duration slaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
           
            
            record.sla_violated_orders_count = self.env['fsm.order'].search_count(domain + [
                ('work_progress_to_done_duration', '>', 0),
                ('estimated_problem_duration', '>', 0),
                ('work_progress_to_done_duration', '>', 'estimated_problem_duration')
            ])
            
    @api.depends('date_from', 'date_to', 'team_id', 'person_id')
    def _compute_duplicate_statistics(self):
        for record in self:
            domain = record._get_base_domain()
            all_orders = self.env['fsm.order'].search(domain)
            
            # العمليات المكررة لنفس العميل
            customer_counts = defaultdict(int)
            for order in all_orders:
                if order.customer_id:
                    customer_id = order.customer_id
                    customer_counts[customer_id] += 1
            
            # عد العمليات (وليس العملاء) للعملاء الذين لديهم أكثر من عملية واحدة
            duplicate_customer_orders = 0
            for customer_id, count in customer_counts.items():
                if count > 1:
                    duplicate_customer_orders += count  # عد جميع العمليات للعميل المكرر
            record.duplicate_customer_orders_count = duplicate_customer_orders
            
            # العمليات المكررة لنفس رقم الفات
            vat_counts = defaultdict(int)
            for order in all_orders:
                if (order.customer_id and 
                    hasattr(order.customer_id, 'vat_number') and 
                    order.customer_id.vat_number):
                    vat_number = order.customer_id.vat_number
                    vat_counts[vat_number] += 1
            
            # عد العمليات (وليس أرقام الفات) لأرقام الفات التي لديها أكثر من عملية واحدة
            duplicate_vat_orders = 0
            for vat_number, count in vat_counts.items():
                if count > 1:
                    duplicate_vat_orders += count  # عد جميع العمليات لرقم الفات المكرر
            record.duplicate_vat_orders_count = duplicate_vat_orders
          
           

    @api.depends('date_from', 'date_to', 'team_id', 'person_id')
    def _compute_time_statistics(self):
        for record in self:
            domain = record._get_base_domain()
            
            # العمليات التي لم يتم حلها بعد 12 ساعة
            twelve_hours_ago = datetime.now() - timedelta(hours=12)
            unsolved_domain = domain + [
                ('create_date', '<', twelve_hours_ago),
                ('stage_id.is_closed', '=', False)
            ]
            
            unsolved_orders = self.env['fsm.order'].search(unsolved_domain)
            record.unsolved_12h_orders_count = len(unsolved_orders)

    

    
    
    @api.onchange('date_from', 'date_to', 'team_id', 'person_id')
    def _onchange_filters(self):
        """تحديث تلقائي عند تغيير الفلاتر"""
        pass  # سيتم إعادة حساب الحقول تلقائياً
    
    @api.onchange('team_id')
    def _onchange_team_id(self):
        """إعادة تعيين الموظف عند تغيير الفريق"""
        if self.team_id:
            # فلترة الموظفين حسب الفريق المختار
            return {
                'domain': {
                    'person_id': [('team_id', '=', self.team_id.id)]
                }
            }
        else:
            self.person_id = False
            return {
                'domain': {
                    'person_id': []
                }
            }
            
            
    def action_set_today_filter(self):
        """تطبيق فلتر اليوم"""
        today = fields.Date.today()
        self.write({
            'date_from': today,
            'date_to': today
        })
        return self.action_refresh_dashboard()
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'message': 'تم تطبيق فلتر اليوم',
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }
    
    def action_set_week_filter(self):
        """تطبيق فلتر هذا الأسبوع"""
        today = fields.Date.today()
        week_start = today - timedelta(7)
        self.write({
            'date_from': week_start,
            'date_to': today
        })
        return self.action_refresh_dashboard()
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'message': 'تم تطبيق فلتر هذا الأسبوع',
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }
        
        
    def action_set_month_filter(self):
        """تطبيق فلتر هذا الشهر"""
        today = fields.Date.today()
        month_start = today.replace(day=1)
        self.write({
            'date_from': month_start,
            'date_to': today
        })
        return self.action_refresh_dashboard()
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'action':"self.action_refresh_dashboard()",
        #     'params': {
        #         'message': 'تم تطبيق فلتر هذا الشهر',
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }

    def action_refresh_dashboard(self):
        """تحديث الداشبورد"""
        # إعادة حساب جميع الحقول المحسوبة
        self._compute_order_statistics()
        self._compute_duplicate_statistics() 
        self._compute_time_statistics()
        self._compute_employee_statisticss()
        
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'message': 'تم تحديث الداشبورد بنجاح',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_completed_orders(self):
        """عرض العمليات المكتملة"""
        domain = self._get_base_domain()
        orders = self.env['fsm.order'].search(domain)
        cancelled_orders = orders.filtered(lambda o: 'Work Completed' in o.stage_id.name.lower() or 'Completed' in o.stage_id.name.lower() or 'completed' in o.stage_id.name.lower() or 'work completed' in o.stage_id.name.lower() or 'تم العمل' in o.stage_id.name)
        
        return self._open_orders_view([('id', 'in', cancelled_orders.ids)], 'العمليات المكتملة')

    def action_view_cancelled_orders(self):
        """عرض العمليات الملغية"""
        domain = self._get_base_domain()
        orders = self.env['fsm.order'].search(domain)
        cancelled_orders = orders.filtered(lambda o: 'ملغي' in o.stage_id.name.lower() or 'Cancelled' in o.stage_id.name)
        return self._open_orders_view([('id', 'in', cancelled_orders.ids)], 'العمليات الملغية')

    def action_view_in_progress_orders(self):
        """عرض العمليات جاري العمل"""
        domain = self._get_base_domain()
        orders = self.env['fsm.order'].search(domain)
        progress_orders = orders.filtered(lambda o: 'Work in Progress' in o.stage_id.name.lower() or 'work in progress' in o.stage_id.name.lower() or  'جاري العمل' in o.stage_id.name)
        return self._open_orders_view([('id', 'in', progress_orders.ids)], 'جاري العمل')

    def action_view_postponed_orders(self):
        """عرض العمليات المؤجلة"""
        # domain = self._get_base_domain() + [('stage_id.name', '=', "Postponed")]
        # return self._open_orders_view(domain, 'العمليات المؤجلة')
        domain = self._get_base_domain()
        orders = self.env['fsm.order'].search(domain)
        
        postponed_orders = orders.filtered(lambda o: 'Postponed' in o.stage_id.name.lower() or 'postponed' in o.stage_id.name.lower() or 'المؤجلة' in o.stage_id.name or 'مؤجل' in o.stage_id.name)
        return self._open_orders_view([('id', 'in', postponed_orders.ids)], 'العمليات المؤجلة')

    def action_view_unsolved_12h_orders(self):
        """عرض العمليات غير المحلولة بعد 12 ساعة"""
        twelve_hours_ago = datetime.now() - timedelta(hours=12)
        domain = self._get_base_domain() + [
            ('create_date', '<', twelve_hours_ago),
            ('stage_id.is_closed', '=', False)
        ]
        return self._open_orders_view(domain, 'العمليات غير المحلولة بعد 12 ساعة')
    
    
    
    def action_view_sla_violated_orders(self):
        self.ensure_one()
        domain = self._get_base_domain()
        domain += [('work_progress_to_done_duration', '>', 0),
                   ('estimated_problem_duration', '>', 0),
                ('work_progress_to_done_duration', '>', 'estimated_problem_duration')]
        return {
            'name': 'SLA Violated Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }

    def action_view_duplicate_customer_orders(self):
        """عرض العمليات المكررة لنفس العميل"""
        domain = self._get_base_domain()
        all_orders = self.env['fsm.order'].search(domain)
        
        # العثور على العملاء الذين لديهم أكثر من عملية واحدة
        customer_counts = defaultdict(list)
        for order in all_orders:
            if order.customer_id : #and order.location_id.partner_id
                customer_id = order.customer_id
                customer_counts[customer_id].append(order.id)
        
        # الحصول على العمليات للعملاء المكررين
        duplicate_order_ids = []
        for customer_id, order_ids in customer_counts.items():
            if len(order_ids) > 1:  # عميل لديه أكثر من عملية
                duplicate_order_ids.extend(order_ids)
        
        return self._open_orders_view([('id', 'in', duplicate_order_ids)], 'العمليات المكررة لنفس العميل')

    def action_view_duplicate_vat_orders(self):
        """عرض العمليات المكررة لنفس رقم الفات"""
        domain = self._get_base_domain()
        all_orders = self.env['fsm.order'].search(domain)
        
        # العثور على أرقام الفات التي لديها أكثر من عملية واحدة
        vat_counts = defaultdict(list)
        for order in all_orders:
            if (order.customer_id and 
                hasattr(order.customer_id, 'vat_number') and 
                order.customer_id.vat_number):
                vat_number = order.customer_id.vat_number
                vat_counts[vat_number].append(order.id)
   
        # الحصول على العمليات لأرقام الفات المكررة
        duplicate_order_ids = []
        for vat_number, order_ids in vat_counts.items():
            if len(order_ids) > 1:  # رقم فات لديه أكثر من عملية
                duplicate_order_ids.extend(order_ids)
        
        return self._open_orders_view([('id', 'in', duplicate_order_ids)], 'العمليات المكررة لنفس رقم الفات')

    def action_view_all_orders(self):
        """عرض جميع العمليات"""
        domain = self._get_base_domain()
        return self._open_orders_view(domain, 'جميع العمليات')

    def _open_orders_view(self, domain, title):
        """فتح view العمليات"""
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': self.env.context,
            'target': 'current',
        }