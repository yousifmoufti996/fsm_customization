# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError 

print("=== FSM ORDER MODEL FILE IS LOADING ===")
class FSMOrder(models.Model):
    _inherit = 'fsm.order'
    print("=== FSM ORDER MODEL FILE IS LOADIe ===")
    test_user_group = fields.Boolean(
        compute='_compute_test_user_group',
        string='Test User Group'
    )

    @api.depends_context('uid')  
    def _compute_test_user_group(self):
        print("=== TEST COMPUTE RUNNING ===")
        for record in self:
            record.test_user_group = True
        print("=== TEST COMPUTE DONE ===")
        
        
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True
    )

    customer_total_due = fields.Monetary(
        string='Total Due',
        related='customer_id.total_due',   # <-- points to the partner’s field
        readonly=True,
        currency_field='currency_id'
    )

    customer_status = fields.Selection(
        related='customer_id.status',
        string='Status',
        readonly=True
    )
    
    customer_number_of_expired_days = fields.Integer(
        related='customer_id.number_of_expired_days',
        string='Number of Expired Days',
        readonly=True
    )
    # reason = fields.Text(string="السبب", tracking=True)

    # Add reason field that becomes mandatory for specific stages
    stage_reason = fields.Text(string='سبب تغيير المرحلة',
        tracking=True,
        help="مطلوب عند: الإلغاء، التأجيل، التوقف الطارئ، المتابعة التسويقية والمبيعات"
        )
    
    type_operation_reason = fields.Text(
        string="سبب نوع العملية", 
        tracking=True,
        help="تبرير اختيار نوع العملية والعملية المحددة"
    )
    user_is_manager = fields.Boolean(
        compute='_compute_user_permissions',
        string='User is Manager of this Order'
    )
    user_is_callcenter = fields.Boolean(
        compute='_compute_user_permissions',
        # compute='_compute_user_is_callcenter',
        string='User is Call Center'
    )
    user_is_auditor = fields.Boolean(
        compute='_compute_user_is_auditor',
        string='User is auditor'
    )
    is_new_record = fields.Boolean(compute="_compute_is_new")

    def _compute_is_new(self):
        for rec in self:
            rec.is_new_record = not bool(rec.id)
    
    
    @api.depends_context('uid')
    def _compute_user_is_auditor(self):
        for record in self:
            record.user_is_auditor = self.env.user.has_group('fsm_customization.group_fsm_auditor') or False
            
    user_is_admin = fields.Boolean(
        # compute='_compute_user_is_admin',
        compute='_compute_user_permissions',
        string='User is Administrator'
    )
    
    @api.depends('manager_id')
    @api.depends_context('uid')
    def _compute_user_permissions(self):
        """Compute user permissions for access control"""
        print("=== COMPUTING USER PERMISSIONS ===")
        print(f"Current user: {self.env.user.name}")
        print(f"Current user ID: {self.env.user.id}")
        
        for record in self:
            is_callcenter = self.env.user.has_group('fsm_customization.group_callcenter_user')
            is_admin = self.env.user.has_group('base.group_system')
            is_manager = (record.manager_id.user_id.id == self.env.user.id) if record.manager_id and record.manager_id.user_id else False
        
            print(f"Has callcenter group: {is_callcenter}")
            print(f"Has admin group: {is_admin}")
            print(f"is_manager : {is_manager}")
            
            record.user_is_callcenter = is_callcenter
            record.user_is_admin = is_admin
            record.user_is_manager = is_manager
            
        print("=== END COMPUTING ===")

    
    estimated_problem_duration = fields.Float(
        string='Estimated Duration (Hours)', 
        help='Duration estimated based on problem type',
        digits=(16, 4)
    )

    estimated_problem_duration_display = fields.Char(
        string='Duration (HH:MM:SS)', 
        default="00:00:00",
        help='Duration estimated based on problem type'
    )

    @api.onchange('estimated_problem_duration_display')
    def _onchange_estimated_problem_duration_display(self):
        """Update hours when user edits the HH:MM:SS field"""
        if self.estimated_problem_duration_display:
            try:
                time_parts = self.estimated_problem_duration_display.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    self.estimated_problem_duration = hours + (minutes / 60.0) + (seconds / 3600.0)
                elif len(time_parts) == 2:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    self.estimated_problem_duration = hours + (minutes / 60.0)
            except (ValueError, IndexError):
                self.estimated_problem_duration = 0.0

    @api.onchange('problem_type_id')
    def _onchange_problem_type_id(self):
        """Update duration, clear solution, and set domain when problem type changes"""
        if self.problem_type_id:
            if self.problem_type_id.estimated_duration:
                print(f"Problem type estimated_duration: {self.problem_type_id.estimated_duration}")
                
                # Set the hours field directly
                self.estimated_problem_duration = self.problem_type_id.estimated_duration
                
                # Convert to HH:MM:SS format for display
                total_seconds = int(self.problem_type_id.estimated_duration * 3600)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                self.estimated_problem_duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                print(f"Set estimated_problem_duration to: {self.estimated_problem_duration}")
                print(f"Set estimated_problem_duration_display to: {self.estimated_problem_duration_display}")
            else:
                self.estimated_problem_duration = 0.0
                self.estimated_problem_duration_display = "00:00:00"
                print("No estimated duration in problem type, set to 0.0")

            # Clear the solution field
            self.problem_solution_id = False

            return {
                'domain': {
                    'problem_solution_id': [('problem_type_id', '=', self.problem_type_id.id)]
                }
            }
        else:
            self.estimated_problem_duration = 0.0
            self.estimated_problem_duration_display = "00:00:00"
            print("No problem type selected, set duration to 0.0")
            
            self.problem_solution_id = False
            
            return {
                'domain': {
                    'problem_solution_id': []
                }
            }


                
        
    @api.model
    def _group_expand_stages(self, stages, domain, order):
        return stages.search([], order=order)
    # Contact Details - Related fields from customer
    customer_name = fields.Char(related='customer_id.name', string='الاسم الرباعي واللقب', readonly=True)
    customer_email = fields.Char(related='customer_id.email', string='Email', readonly=True)
    customer_phone = fields.Char(related='customer_id.phone', string='رقم التلفون الاول', readonly=True)
    customer_mobile = fields.Char(related='customer_id.mobile', string='رقم التلفون الثاني', readonly=True)
    customer_street = fields.Char(related='customer_id.area_name_id.name', string='اسم المنطقة', readonly=True)
    customer_street2 = fields.Char(related='customer_id.street2', string='اقرب نقطة دالة', readonly=True)
    customer_zip = fields.Char(related='customer_id.area_number_id.name', string='رقم المنطقة', readonly=True)
    customer_user_name = fields.Char(related='customer_id.user_name', string='User Name', readonly=True)
    
    customer_category_id = fields.Many2many(related='customer_id.category_id', string='Subscription Type', readonly=True)
    customer_menu_type_ids = fields.Many2many(related='customer_id.menu_type_ids', string='مجموع عملاء فرعية', readonly=True)
    @api.onchange('customer_menu_type_ids')
    def _onchange_customer_menu_type_ids(self):
        if self.customer_menu_type_ids:
            # Keep only the last selected
            self.customer_menu_type_ids = self.customer_menu_type_ids[-1]
            
    customer_city = fields.Char(related='customer_id.city', string='City', readonly=True)
    customer_local_number = fields.Char(related='customer_id.local_number', string='رقم المحلة', readonly=True)
    customer_family_number = fields.Char(related='customer_id.family_number', string='الرقم العائلي', readonly=True)
    customer_pole = fields.Char(related='customer_id.pole', string='العمود', readonly=True)
    
    customer_mother_name_and_surname = fields.Char(related='customer_id.mother_name_and_surname', string='اسم الام الثلاثي واللقب', readonly=True)
    customer_home_number = fields.Char(related='customer_id.home_number', string='رقم المنزل', readonly=True)
    customer_contract_number = fields.Char(related='customer_id.contract_number', string='رقم العقد', readonly=True)
    customer_alley_number = fields.Char(related='customer_id.alley_number', string='رقم الزقاق', readonly=True)
    customer_house_number = fields.Char(related='customer_id.house_number', string='رقم الدار', readonly=True)
    customer_voucher_number = fields.Char(related='customer_id.voucher_number', string='رقم الوصل', readonly=True)
    customer_vat_number = fields.Integer(related='customer_id.vat_number', string='رقم الفات', readonly=True)
    customer_residence_card = fields.Char(related='customer_id.residence_card', string='بطاقة السكن', readonly=True)
    customer_id_card = fields.Char(related='customer_id.id_card', string='بطاقة الهوية', readonly=True)
    customer_port_number = fields.Integer(related='customer_id.port_number', string='رقم البورت', readonly=True)
    # Override existing fields to add tracking
    # stage_id = fields.Many2one(tracking=True)
    person_id = fields.Many2one(tracking=True)
    customer_id = fields.Many2one(tracking=True)
    scheduled_date_start = fields.Datetime(tracking=True)
    scheduled_date_end = fields.Datetime(tracking=True)
    date_start = fields.Datetime(tracking=True)
    date_end = fields.Datetime(tracking=True)
    priority = fields.Selection(tracking=True)
    description = fields.Text(tracking=True)
    resolution = fields.Text(tracking=True)
    
    problem_type_id = fields.Many2one(
        'problem.type',
        string="نوع المشكلة",
        # required=True,
        tracking=True
    )
    problem_solution_id = fields.Many2one(
        'problem.solution',
        string="الحل",
        domain="[('problem_type_id', '=', problem_type_id)]",
        # required=True,
        tracking=True
    )
    solution_description = fields.Text(
        string="تفاصيل الحل",
        related="problem_solution_id.description"
    )
    
   

    @api.constrains('problem_type_id', 'problem_solution_id')
    def _check_solution_problem_type(self):
        """Ensure the selected solution belongs to the selected problem type"""
        for record in self:
            if record.problem_solution_id and record.problem_type_id:
                if record.problem_solution_id.problem_type_id != record.problem_type_id:
                    raise ValidationError(
                        _("الحل المختار لا ينتمي لنوع المشكلة المحدد")
                    )
  

    
    
    
    @api.constrains('stage_id', 'stage_reason')
    def _check_stage_reason_required(self):
        """Make reason mandatory for specific stages"""
        for record in self:
            #Required Only at Completion Stage
            if record.stage_id.name == 'طلب اتمام العمل':
                if (record.type or record.operation_type_id) and not record.type_operation_reason:
                    raise ValidationError("سبب نوع العملية مطلوب عند طلب إتمام العمل")
            if record.stage_id:
                stage_name = record.stage_id.name
                required_reason_stages = [
                    'ملغي',           # Cancelled
                    'توقف طارئ',      # Emergency Stop
                    'مؤجل',          # Postponed
                    'متابعة التسويق', # Marketing Follow-up
                    'متابعة المبيعات' # Sales Follow-up
                ]
                
                if stage_name in required_reason_stages and not record.stage_reason:
                    raise ValidationError(_('السبب مطلوب عند اختيار مرحلة: %s') % stage_name)


    
    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Clear reason if stage doesn't require it"""
        if self.stage_id:
            stage_name = self.stage_id.name
            required_reason_stages = [
                'ملغي',           # Cancelled
                'توقف طارئ',      # Emergency Stop
                'مؤجل',          # Postponed
                'متابعة التسويق', # Marketing Follow-up
                'متابعة المبيعات' # Sales Follow-up
            ]
            
            if stage_name not in required_reason_stages:
                self.stage_reason = False
                
                
  
    # Contract Details - Editable fields with Arabic names
    temp_area_name = fields.Many2one(
        'area.name',
        string="اسم المنطقة",
        options="{'no_create': True, 'no_create_edit': True}"
    )
    # temp_area_number = fields.Char(string="رقم المنطقة")
    temp_area_number = fields.Many2one(
        'area.number',
        string="رقم المنطقة",
        domain="[('area_name_id', '=', temp_area_name)]",
        # options="{'no_create': True, 'no_create_edit': True}"
    )
    temp_home_number = fields.Char(string="رقم المنزل")
    temp_nearest_point = fields.Char(string="اقرب نقطة دالة")
    temp_longitude_coordinates = fields.Float(string="احداثيات الطول", digits=(10, 6))
    temp_latitude_coordinates = fields.Float(string="احداثيات العرض", digits=(10, 6))
    temp_local_number = fields.Char(string="رقم المحلة")
    temp_alley_number = fields.Char(string="رقم الزقاق")
    temp_house_number = fields.Char(string="رقم الدار")
    temp_vat_number = fields.Integer(string="رقم الفات")
    temp_port_number = fields.Integer(string="رقم البورت")
    temp_full_name_and_surname = fields.Char(string="الاسم رباعي واللقب")
    temp_mother_name_and_surname = fields.Char(string="اسم الام الثلاثي واللقب")
    temp_first_phone_number = fields.Char(string="رقم الهاتف الاول")
    temp_second_phone_number = fields.Char(string="رقم الهاتف الثاني")
    temp_email1 = fields.Char(string="البريد الالكتروني")
    temp_subscription_type = fields.Many2many(
        'res.partner.category',
        'fsm_order_subscription_type_rel',
        'fsm_order_id',
        'category_id',
        string="نوع الاشتراك"
    )
    def load_customer_to_contract(self):
        """Load customer data into contract fields"""
        if not self.customer_id:
            return
        
        self.temp_full_name_and_surname = self.customer_id.full_name_and_surname
        self.temp_mother_name_and_surname = self.customer_id.mother_name_and_surname
        self.temp_user_name = self.customer_id.user_name
        self.temp_first_phone_number = self.customer_id.first_phone_number
        self.temp_second_phone_number = self.customer_id.second_phone_number
        self.temp_email1 = self.customer_id.email1
        self.temp_area_name = self.customer_id.area_name_id
        self.temp_area_number = self.customer_id.area_number_id
        self.temp_home_number = self.customer_id.home_number
        self.temp_nearest_point = self.customer_id.nearest_point
        self.temp_latitude_coordinates = self.customer_id.partner_latitude
        self.temp_longitude_coordinates = self.customer_id.partner_longitude
        self.temp_local_number = self.customer_id.local_number
        self.temp_alley_number = self.customer_id.alley_number
        self.temp_house_number = self.customer_id.house_number
        self.temp_vat_number = self.customer_id.vat_number
        self.temp_port_number = self.customer_id.port_number
        self.temp_contract_number = self.customer_id.contract_number
        self.temp_voucher_number = self.customer_id.voucher_number
        self.temp_residence_card = self.customer_id.residence_card
        self.temp_id_card = self.customer_id.id_card
        self.temp_family_number = self.customer_id.family_number
        self.temp_subscription_type = self.customer_id.category_id
        self.temp_menu_type_ids = self.customer_id.menu_type_ids
        self.contract_changes_pending = False
   
        
    temp_contract_number = fields.Char(string="رقم العقد")
    temp_voucher_number = fields.Char(string="رقم الوصل")
    temp_residence_card = fields.Char(string="بطاقة السكن")
    temp_menu_type_ids = fields.Many2many( related='customer_id.menu_type_ids', string='مجموع عملاء فرعية', readonly=False)
    @api.onchange('temp_menu_type_ids')
    def _onchange_temp_menu_type_ids(self):
        if self.temp_menu_type_ids:
            # Keep only the last selected
            self.temp_menu_type_ids = self.temp_menu_type_ids[-1]
    
  
    temp_id_card = fields.Char(string="بطاقة الهوية")
    temp_family_number = fields.Char(string="الرقم العائلي")
    temp_user_name = fields.Char(string="User Name")

    # Status tracking
    contract_changes_pending = fields.Boolean(string='Contract Changes Pending', default=False)
    contract_approved_by = fields.Many2one('res.users', string='Contract Approved By', readonly=True)
    contract_approved_date = fields.Datetime(string='Contract Approved Date', readonly=True)

    @api.onchange('customer_id')
    def _onchange_customer_id_load_contract(self):
        """Load customer data into contract fields when customer changes"""
        if self.customer_id:
            # Load existing customer data into temporary fields for editing
            # self.temp_area_name = getattr(self.customer_id, 'area_name', '') or ''
            self.temp_area_name = self.customer_id.area_name_id
            # self.temp_area_number = getattr(self.customer_id, 'area_number', '') or ''
            self.temp_area_number = self.customer_id.area_number_id
            self.temp_home_number = getattr(self.customer_id, 'home_number', '') or ''
            self.temp_nearest_point = getattr(self.customer_id, 'nearest_point', '') or ''
            self.temp_longitude_coordinates = getattr(self.customer_id, 'longitude_coordinates', 0.0) or 0.0
            self.temp_latitude_coordinates = getattr(self.customer_id, 'latitude_coordinates', 0.0) or 0.0
            self.temp_local_number = getattr(self.customer_id, 'local_number', '') or ''
            self.temp_alley_number = getattr(self.customer_id, 'alley_number', '') or ''
            self.temp_house_number = getattr(self.customer_id, 'house_number', '') or ''
            self.temp_vat_number = getattr(self.customer_id, 'vat_number', 0) or 0
            self.temp_port_number = getattr(self.customer_id, 'port_number', 0) or 0
            self.temp_full_name_and_surname = getattr(self.customer_id, 'full_name_and_surname', '') or ''
            self.temp_mother_name_and_surname = getattr(self.customer_id, 'mother_name_and_surname', '') or ''
            self.temp_first_phone_number = getattr(self.customer_id, 'first_phone_number', '') or self.customer_id.phone or ''
            self.temp_second_phone_number = getattr(self.customer_id, 'second_phone_number', '') or self.customer_id.mobile or ''
            self.temp_email1 = getattr(self.customer_id, 'email1', '') or self.customer_id.email or ''
            # self.temp_subscription_type = getattr(self.customer_id, 'subscription_type', '') or ''
            self.temp_subscription_type = self.customer_id.category_id
            self.temp_contract_number = getattr(self.customer_id, 'contract_number', '') or ''
            self.temp_voucher_number = getattr(self.customer_id, 'voucher_number', '') or ''
            self.temp_residence_card = getattr(self.customer_id, 'residence_card', '') or ''
            self.temp_menu_type_ids = getattr(self.customer_id, 'menu_type_ids', '') or False
            self.temp_id_card = getattr(self.customer_id, 'id_card', '') or ''
            self.temp_family_number = getattr(self.customer_id, 'family_number', '') or ''
            self.temp_user_name = getattr(self.customer_id, 'user_name', '') or ''
            
            # Reset pending changes flag
            self.contract_changes_pending = False
        else:
            # Clear all fields if no customer selected
            self.action_reset_contract_fields()

    @api.onchange('temp_area_name', 'temp_area_number', 'temp_home_number', 
                'temp_nearest_point', 'temp_longitude_coordinates', 'temp_latitude_coordinates',
                'temp_local_number', 'temp_alley_number', 'temp_house_number',
                'temp_vat_number', 'temp_port_number', 'temp_full_name_and_surname',
                'temp_mother_name_and_surname', 'temp_first_phone_number', 'temp_second_phone_number',
                'temp_email1', 'temp_subscription_type', 'temp_contract_number',
                'temp_voucher_number', 'temp_residence_card', 'temp_id_card', 'temp_family_number', 'temp_user_name', 'temp_menu_type_ids')
    def _onchange_contract_fields(self):
        """Mark changes as pending when contract fields are modified"""
        if any([
            self.temp_area_name, self.temp_area_number, self.temp_home_number,
            self.temp_nearest_point, self.temp_longitude_coordinates, self.temp_latitude_coordinates,
            self.temp_local_number, self.temp_alley_number, self.temp_house_number,
            self.temp_vat_number, self.temp_port_number, self.temp_full_name_and_surname,
            self.temp_mother_name_and_surname, self.temp_first_phone_number, self.temp_second_phone_number,
            self.temp_email1, self.temp_subscription_type, self.temp_contract_number,
            self.temp_voucher_number, self.temp_residence_card,self.temp_menu_type_ids, self.temp_id_card, self.temp_family_number, self.temp_user_name
        ]):
            self.contract_changes_pending = True

    @api.onchange('temp_area_name')
    def _onchange_temp_area_name(self):
        """Clear area number when area name changes"""
        if self.temp_area_name != self._origin.temp_area_name:
            self.temp_area_number = False


    def action_approve_contract_changes(self):
        """Approve and save contract changes to res.partner"""
        print("لا يمكن اعتماد تغييرات العقد لأحد المشرفين")
        print("self.env.user._is_admin()",self.env.user._is_admin())
        print('self.manager_id',self.manager_id)
        print('self.env.user',self.env.user)
        manager_user_id = self.manager_id.user_id.id if self.manager_id and self.manager_id.user_id else False
        if not (manager_user_id == self.env.user.id or self.env.user._is_admin() or self.user_is_callcenter):
            raise UserError("فقط المشرف أو الإدارة أو مركز الاتصال يمكنه اعتماد تغييرات العقد")
        
        print(self.temp_full_name_and_surname)
        if not self.customer_id:
            raise UserError("لا يوجد عميل محدد لتحديث بياناته.")

        # Prepare update values for res.partner
        update_vals = {}
        
        # Map temporary fields to partner fields
        if self.temp_area_name:
            update_vals['area_name_id'] = self.temp_area_name.id
            update_vals['area_name'] = self.temp_area_name.name
        if self.temp_area_number:
            update_vals['area_number_id'] = self.temp_area_number.id
            update_vals['area_number'] = self.temp_area_number.name
        if self.temp_home_number:
            update_vals['home_number'] = self.temp_home_number
        if self.temp_nearest_point:
            update_vals['nearest_point'] = self.temp_nearest_point
            update_vals['street2'] = self.temp_nearest_point
        if self.temp_longitude_coordinates:
            update_vals['partner_longitude'] = self.temp_longitude_coordinates
        if self.temp_latitude_coordinates:
            update_vals['partner_latitude'] = self.temp_latitude_coordinates 
      
        if self.temp_local_number:
            update_vals['local_number'] = self.temp_local_number
        if self.temp_alley_number:
            update_vals['alley_number'] = self.temp_alley_number
        if self.temp_house_number:
            update_vals['house_number'] = self.temp_house_number
        if self.temp_vat_number:
            update_vals['vat_number'] = self.temp_vat_number
        if self.temp_port_number:
            update_vals['port_number'] = self.temp_port_number
        if self.temp_family_number:  
            update_vals['family_number'] = self.temp_family_number
        if self.temp_user_name:  
            update_vals['user_name'] = self.temp_user_name
        print("sif self.temp_full_name_and_surname:")
        if self.temp_full_name_and_surname:
            update_vals['full_name_and_surname'] = self.temp_full_name_and_surname
            print(self.temp_full_name_and_surname ,"update_vals['full_name_and_surname'] = self.temp_full_name_and_surname")
        if self.temp_mother_name_and_surname:
            update_vals['mother_name_and_surname'] = self.temp_mother_name_and_surname
        if self.temp_first_phone_number:
            update_vals['first_phone_number'] = self.temp_first_phone_number
            update_vals['phone'] = self.temp_first_phone_number  # Also update standard phone
        if self.temp_second_phone_number:
            update_vals['second_phone_number'] = self.temp_second_phone_number
            update_vals['mobile'] = self.temp_second_phone_number  # Also update standard mobile
        if self.temp_email1:
            update_vals['email1'] = self.temp_email1
            update_vals['email'] = self.temp_email1  # Also update standard email
        if self.temp_subscription_type:
            # update_vals['subscription_type'] = self.temp_subscription_type
            update_vals['category_id'] = [(6, 0, self.temp_subscription_type.ids)]
        if self.temp_contract_number:
            update_vals['contract_number'] = self.temp_contract_number
        if self.temp_voucher_number:
            update_vals['voucher_number'] = self.temp_voucher_number
        if self.temp_residence_card:
            update_vals['residence_card'] = self.temp_residence_card
        if self.temp_menu_type_ids:
            update_vals['menu_type_ids'] = self.temp_menu_type_ids
        if self.temp_id_card:
            update_vals['id_card'] = self.temp_id_card

        # Update the customer/partner with new values
        print(" if update_vals:")
        
        if update_vals:
            print("update_vals",update_vals)
            self.customer_id.write(update_vals)
            
            # Log the changes in the FSM order
            changed_fields = []
            for field_name, new_value in update_vals.items():
                if field_name not in ['phone', 'mobile', 'email']:  # Skip duplicate standard fields
                    changed_fields.append(f"{field_name}: {new_value}")
            
            change_log = "تم تحديث معلومات العقد:\n" + "\n".join(changed_fields)
            
            self.message_post(
                body=change_log,
                subject="تحديث معلومات العقد",
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        # Update FSM order status
        self.contract_changes_pending = False
        self.contract_approved_by = self.env.user
        self.contract_approved_date = fields.Datetime.now()
        

        # Return action to refresh the current record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': self.env.context
        }

    def action_reset_contract_fields(self):
        """Reset all contract fields"""
        reset_vals = {
            'temp_area_name': False,
            'temp_area_number': False,
            'temp_home_number': '',
            'temp_nearest_point': '',
            'temp_longitude_coordinates': 0.0,
            'temp_latitude_coordinates': 0.0,
            'temp_local_number': '',
            'temp_alley_number': '',
            'temp_house_number': '',
            'temp_vat_number': 0,
            'temp_port_number': 0,
            'temp_full_name_and_surname': '',
            'temp_mother_name_and_surname': '',
            'temp_first_phone_number': '',
            'temp_second_phone_number': '',
            'temp_email1': '',
            'temp_subscription_type': False,
            'temp_contract_number': '',
            'temp_voucher_number': '',
            'temp_residence_card': '',
            'temp_menu_type_ids': False,
            'temp_id_card': '',
            'temp_family_number': '',
            'temp_user_name': '',
            'contract_changes_pending': False,
        }
        
        self.write(reset_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'تم إعادة التعيين',
                'message': 'تم إعادة تعيين جميع حقول العقد.',
                'type': 'info',
            }
        }
    def _convert_display_to_hours(self, display_val):
        """Convert HH:MM:SS display to hours"""
        if display_val:
            try:
                time_parts = display_val.split(':')
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    return hours + (minutes / 60.0) + (seconds / 3600.0)
                elif len(time_parts) == 2:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    return hours + (minutes / 60.0)
            except (ValueError, IndexError):
                pass
        return 0.0
    
    @api.model
    def create(self, vals):
        """Override create to handle duration fields"""
        # Handle duration display field during create
        if 'estimated_problem_duration_display' in vals and not vals.get('estimated_problem_duration'):
            display_val = vals.get('estimated_problem_duration_display', '00:00:00')
            vals['estimated_problem_duration'] = self._convert_display_to_hours(display_val)
        
        return super().create(vals)
    
    
    def write(self, vals):
        """Override write to implement business rules, field locking, and custom tracking"""
        if 'estimated_problem_duration_display' in vals:
            display_val = vals.get('estimated_problem_duration_display', '00:00:00')
            vals['estimated_problem_duration'] = self._convert_display_to_hours(display_val)
        
        # Check if we're transitioning TO 'تم العمل' stage
        transitioning_to_completed = False
        if 'stage_id' in vals:
            new_stage = self.env['fsm.stage'].browse(vals['stage_id'])
            if new_stage.name == 'تم العمل':
                transitioning_to_completed = True
            
            # Track stage changes (if you still need this method)
            # for order in self:
            #     self._track_stage_change(order, vals['stage_id'])
        
        # Store old values for comparison (for tracking messages)
        old_values = {}
        for record in self:
            old_values[record.id] = {
                'stage_id': record.stage_id,
                'person_id': record.person_id,
                'customer_id': record.customer_id,
                'priority': record.priority,
            }
        
        # Apply business rules for each record
        for record in self:
            # Rule 4: Lock all fields when work is already completed 
            # (except when transitioning TO completed stage)
            if record.stage_id.name == 'تم العمل' and not transitioning_to_completed:
                allowed_fields = {
                    'stage_id', 
                    'fields_locked', 
                    'move_ids',           # Allow move operations
                    'stock_move_ids',     # Allow stock moves
                    'picking_ids',        # Allow picking operations
                    'message_ids',        # Allow message updates
                    'activity_ids',       # Allow activity updates
                    '__last_update',      # System field
                    'write_date',         # System field
                    'write_uid',    # System field
                    'estimated_problem_duration',        
                    'estimated_problem_duration_display'
                }
              
                # Allow only stage changes by authorized users (if needed)
                restricted_fields = set(vals.keys()) - allowed_fields
            
              
            # Rule 5: Manager cannot edit manager assignment for himself
            if 'manager_id' in vals and record.manager_id and record.manager_id.user_id == self.env.user and not self.is_fsm_manager and not self.env.user._is_admin():
                new_manager = self.env['hr.employee'].browse(vals['manager_id']) if vals['manager_id'] else False
                if not new_manager or new_manager.id != record.manager_id.id:
                    raise ValidationError(_(
                        "لا يمكن للمشرف تعديل أو إلغاء حقل إسناد المشرف لنفسه"
                    ))
            
            # Updated auditor check
            if 'resolution' in vals and record.auditor_id and record.auditor_id.user_id == self.env.user and not self.env.user._is_admin():
                raise ValidationError(_(
                    "لا يمكن سوى للمدقق تعديل أو إلغاء حقل resolution"
                ))
            
        # Perform the actual write operation
        result = super().write(vals)
        
        # Lock fields when work is completed
        if 'stage_id' in vals:
            new_stage = self.env['fsm.stage'].browse(vals['stage_id'])
            for record in self:
                if new_stage.name == 'تم العمل':
                    record.sudo().write({'fields_locked': True})
        
        # Add custom tracking messages
        for record in self:
            old_vals = old_values.get(record.id, {})
            
            # Track stage changes with reason
            if 'stage_id' in vals and old_vals.get('stage_id') != record.stage_id:
                stage_msg = _('Stage changed from "%s" to "%s"') % (
                    old_vals.get('stage_id').name if old_vals.get('stage_id') else _('None'),
                    record.stage_id.name if record.stage_id else _('None')
                )
                if record.stage_reason:
                    stage_msg += _('\nReason: %s') % record.stage_reason
                
                record.message_post(
                    body=stage_msg,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            
            # Track person assignment
            if 'person_id' in vals and old_vals.get('person_id') != record.person_id:
                person_msg = _('Assigned person changed from "%s" to "%s"') % (
                    old_vals.get('person_id').name if old_vals.get('person_id') else _('None'),
                    record.person_id.name if record.person_id else _('None')
                )
                record.message_post(
                    body=person_msg,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            
            # Track location changes
            if 'customer_id' in vals and old_vals.get('customer_id') != record.customer_id:
                location_msg = _('Location changed from "%s" to "%s"') % (
                    old_vals.get('customer_id').name if old_vals.get('customer_id') else _('None'),
                    record.customer_id.name if record.customer_id else _('None')
                )
                record.message_post(
                    body=location_msg,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
            
            # Track priority changes
            if 'priority' in vals and old_vals.get('priority') != record.priority:
                priority_labels = dict(record._fields['priority'].selection)
                priority_msg = _('Priority changed from "%s" to "%s"') % (
                    priority_labels.get(old_vals.get('priority'), _('None')),
                    priority_labels.get(record.priority, _('None'))
                )
                record.message_post(
                    body=priority_msg,
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
        
        return result
    
    def action_view_order(self):
        """Open the FSM order form view"""
        return {
            'name': 'FSM Order',
            'type': 'ir.actions.act_window',
            'res_model': 'fsm.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_navigate_to(self):
        """Open navigation to the order location with routing"""
        if self.location_id and self.location_id.partner_latitude and self.location_id.partner_longitude:
            # Return a client action that will handle geolocation and routing
            return {
                'type': 'ir.actions.client',
                'tag': 'fsm_navigate_with_route',
                'params': {
                    'latitude': self.location_id.partner_latitude,
                    'longitude': self.location_id.partner_longitude,
                    'location_name': self.location_id.name,
                    'order_name': self.name,
                }
            }
        else:
            # Fallback notification if no coordinates
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Navigation Error',
                    'message': 'No coordinates found for this location. Please update the location coordinates.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
    def action_open_customer_location_wizard(self):
        """Open wizard to get current location and save it to customer"""
        self.ensure_one()
        if not self.customer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'خطأ',
                    'message': 'لا يوجد عميل محدد لهذا الطلب',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "customer.location.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customer_id": self.customer_id.id,
                "default_fsm_order_id": self.id,
            },
        }