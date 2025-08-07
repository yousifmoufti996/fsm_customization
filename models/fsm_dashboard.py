# fsm_dashboard.py
from odoo import api, fields, models, _
from datetime import datetime, timedelta


class FSMDashboard(models.Model):
    _name = "fsm.dashboard"
    _description = "Field Service Management Dashboard"
    _rec_name = "name"
    _order = "create_date desc"

    name = fields.Char(string="Dashboard Name", default="FSM Dashboard", required=True)
    date_from = fields.Date(string="From Date", default=fields.Date.today)
    date_to = fields.Date(string="To Date", default=fields.Date.today)
    
    # إحصائيات الحالات
    completed_orders_count = fields.Integer(
        string="العمليات المكتملة (تم العمل)",
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
        string="العمليات المؤجلة",
        compute="_compute_order_statistics"
    )
    
    # إحصائيات التكرار
    duplicate_customer_orders_count = fields.Integer(
        string="العمليات المكررة لنفس العميل",
        compute="_compute_duplicate_statistics"
    )
    duplicate_vat_orders_count = fields.Integer(
        string="العمليات المكررة لنفس الفات",
        compute="_compute_duplicate_statistics"
    )
    
    # إحصائيات SLA
    sla_orders_count = fields.Integer(
        string="عدد عمليات SLA",
        compute="_compute_sla_statistics"
    )
    unsolved_12h_orders_count = fields.Integer(
        string="العمليات غير المحلولة بعد 12 ساعة",
        compute="_compute_sla_statistics"
    )
    
    # إحصائيات الموظفين
    employee_statistics_ids = fields.One2many(
        "fsm.dashboard.employee", "dashboard_id",
        string="إحصائيات الموظفين",
        compute="_compute_employee_statistics"
    )
    
    # تفاصيل إضافية
    total_orders_count = fields.Integer(
        string="إجمالي العمليات",
        compute="_compute_order_statistics"
    )
    average_completion_time = fields.Float(
        string="متوسط وقت الإنجاز (ساعات)",
        compute="_compute_performance_metrics"
    )
    customer_satisfaction_rate = fields.Float(
        string="معدل رضا العملاء %",
        digits=(16, 4),
        compute="_compute_performance_metrics"
    )

    @api.depends('date_from', 'date_to')
    def _compute_order_statistics(self):
        for record in self:
            domain = []
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            # العمليات المكتملة - البحث عن المرحلة المكتملة
            completed_stage = self.env['fsm.stage'].search([
                ('stage_type', '=', 'order'),
                ('is_closed', '=', True),
                ('name', 'ilike', 'complete')
            ], limit=1)
            
            completed_domain = domain + [('stage_id', '=', completed_stage.id)] if completed_stage else domain + [('stage_id.is_closed', '=', True)]
            record.completed_orders_count = self.env['fsm.order'].search_count(completed_domain)
            
            # العمليات الملغية
            cancelled_stage = self.env['fsm.stage'].search([
                ('stage_type', '=', 'order'),
                ('name', 'ilike', 'cancel')
            ], limit=1)
            
            cancelled_domain = domain + [('stage_id', '=', cancelled_stage.id)] if cancelled_stage else []
            record.cancelled_orders_count = self.env['fsm.order'].search_count(cancelled_domain)
            
            # العمليات جاري العمل - البحث في project.task
            in_progress_tasks = self.env['project.task'].search([
                ('work_in_progress', '=', True)
            ] + ([('create_date', '>=', record.date_from)] if record.date_from else []) +
              ([('create_date', '<=', record.date_to)] if record.date_to else []))
            
            record.in_progress_orders_count = len(in_progress_tasks)
            
            # العمليات المؤجلة
            postponed_tasks = self.env['project.task'].search([
                ('postponement_request', '=', True)
            ] + ([('create_date', '>=', record.date_from)] if record.date_from else []) +
              ([('create_date', '<=', record.date_to)] if record.date_to else []))
            
            record.postponed_orders_count = len(postponed_tasks)
            
            # إجمالي العمليات
            record.total_orders_count = self.env['fsm.order'].search_count(domain)

    @api.depends('date_from', 'date_to')
    def _compute_duplicate_statistics(self):
        for record in self:
            domain = []
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            # العمليات المكررة لنفس العميل
            orders = self.env['fsm.order'].search(domain)
            customer_counts = {}
            for order in orders:
                if order.location_id.partner_id:
                    partner_id = order.location_id.partner_id.id
                    customer_counts[partner_id] = customer_counts.get(partner_id, 0) + 1
            
            duplicate_customers = sum(1 for count in customer_counts.values() if count > 1)
            record.duplicate_customer_orders_count = duplicate_customers
            
            # العمليات المكررة لنفس رقم الفات
            vat_counts = {}
            for order in orders:
                # البحث عن رقم الفات من partner
                partner = order.location_id.partner_id
                if partner and hasattr(partner, 'vat_number') and partner.vat_number:
                    vat_num = partner.vat_number
                    vat_counts[vat_num] = vat_counts.get(vat_num, 0) + 1
            
            duplicate_vats = sum(1 for count in vat_counts.values() if count > 1)
            record.duplicate_vat_orders_count = duplicate_vats

    @api.depends('date_from', 'date_to')
    def _compute_sla_statistics(self):
        for record in self:
            domain = []
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            # عمليات SLA - العمليات التي تجاوزت الوقت المحدد
            # sla_violated_orders = self.env['fsm.order'].search(domain + [
            #     ('request_late', '<', fields.Datetime.now()),
            #     ('stage_id.is_closed', '=', False)
            # ])
            # record.sla_orders_count = len(sla_violated_orders)
            
            # العمليات غير المحلولة بعد 12 ساعة
            twelve_hours_ago = datetime.now() - timedelta(hours=12)
            unsolved_orders = self.env['fsm.order'].search(domain + [
                ('create_date', '<', twelve_hours_ago),
                ('stage_id.is_closed', '=', False)
            ])
            record.unsolved_12h_orders_count = len(unsolved_orders)

    @api.depends('date_from', 'date_to')
    def _compute_employee_statistics(self):
        for record in self:
            # حذف الإحصائيات السابقة
            record.employee_statistics_ids.unlink()
            
            domain = []
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            # جمع إحصائيات كل موظف
            employees = self.env['fsm.person'].search([])
            employee_stats = []
            
            for employee in employees:
                emp_orders = self.env['fsm.order'].search(domain + [
                    ('person_id', '=', employee.id)
                ])
                
                if emp_orders:
                    completed_orders = emp_orders.filtered(lambda o: o.stage_id.is_closed)
                    
                    employee_stats.append({
                        'dashboard_id': record.id,
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'total_orders': len(emp_orders),
                        'completed_orders': len(completed_orders),
                        'pending_orders': len(emp_orders) - len(completed_orders),
                        'completion_rate': (len(completed_orders) / len(emp_orders) * 100) if emp_orders else 0,
                    })
            
            # إنشاء سجلات الإحصائيات
            for stat in employee_stats:
                self.env['fsm.dashboard.employee'].create(stat)

    @api.depends('date_from', 'date_to')
    def _compute_performance_metrics(self):
        for record in self:
            domain = []
            if record.date_from:
                domain.append(('create_date', '>=', record.date_from))
            if record.date_to:
                domain.append(('create_date', '<=', record.date_to))
            
            completed_orders = self.env['fsm.order'].search(domain + [
                ('stage_id.is_closed', '=', True),
                ('date_start', '!=', False),
                ('date_end', '!=', False)
            ])
            
            if completed_orders:
                total_duration = sum(completed_orders.mapped('duration'))
                record.average_completion_time = total_duration / len(completed_orders) if completed_orders else 0
                
                # معدل رضا العملاء (مثال - يمكن تخصيصه حسب الحاجة)
                record.customer_satisfaction_rate = 85.0  # قيمة افتراضية
            else:
                record.average_completion_time = 0
                record.customer_satisfaction_rate = 0

    def refresh_dashboard(self):
        """تحديث الداشبورد"""
        self._compute_order_statistics()
        self._compute_duplicate_statistics()
        self._compute_sla_statistics()
        self._compute_employee_statistics()
        self._compute_performance_metrics()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class FSMDashboardEmployee(models.Model):
    _name = "fsm.dashboard.employee"
    _description = "FSM Dashboard Employee Statistics"
    _rec_name = "employee_name"

    dashboard_id = fields.Many2one("fsm.dashboard", string="Dashboard", ondelete="cascade")
    employee_id = fields.Many2one("fsm.person", string="الموظف")
    employee_name = fields.Char(string="اسم الموظف")
    total_orders = fields.Integer(string="إجمالي العمليات")
    completed_orders = fields.Integer(string="العمليات المكتملة")
    pending_orders = fields.Integer(string="العمليات المعلقة")
    completion_rate = fields.Float(string="معدل الإنجاز %", digits=(16, 4))
    
    # إحصائيات إضافية للموظف
    avg_completion_time = fields.Float(string="متوسط وقت الإنجاز (ساعات)", digits=(16, 4))
    customer_rating = fields.Float(string="تقييم العملاء", digits=(16, 4))