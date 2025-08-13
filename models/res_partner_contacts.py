from odoo import fields, models, api
from odoo.exceptions import ValidationError
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Your existing fields...
    area_name_id = fields.Many2one(
        "area.name",
        'اسم المنطقة'
    )
    user_name = fields.Char("User Name")
    
    @api.onchange('area_name_id')
    def _onchange_area_name_id(self):
        # Clear the menu_type_ids when area changes
        if self.area_name_id:
            self.menu_type_ids = False 
    # Add unique constraint
    _sql_constraints = [
        ('user_name_unique', 'UNIQUE(user_name)', 'اسم المستخدم موجود بالفعل! يرجى اختيار اسم مستخدم آخر.')
    ]
    
    # Add area_number_id field
    area_number_id = fields.Many2one(
        "area.number",
        string="رقم المنطقة",
        domain="[('area_name_id', '=', area_name_id)]"  # Filter by selected area
    )
    
    # Related fields to sync with old module - these will sync with your old module's char fields
    area_name = fields.Char(
        "اسم المنطقة",
        related="area_name_id.name",
        readonly=False,
        store=True
    )
    
    area_number = fields.Char(
        "رقم المنطقة",
        related="area_number_id.name",
        readonly=False,
        store=True
    )

    nearest_point = fields.Char(
        "اقرب نقطة دالة ",
        related="street2",
        readonly=False,
        store=True
    )

    longitude_coordinates = fields.Float(
        "احداثيات الطول ",
        related="partner_longitude",
        readonly=False,
        store=True,
        digits=(10, 6)
    )

    latitude_coordinates = fields.Float(
        "احداثيات العرض", 
        related="partner_latitude",
        readonly=False,
        store=True,
        digits=(10, 6)
    )

    google_maps_url = fields.Char(
        string="Google Maps URL",
        compute="_compute_google_maps_url"
    )

    full_name_and_surname = fields.Char(
        "الاسم رباعي واللقب ",
        related="name",
        readonly=False,
        store=True
    )
    first_phone_number = fields.Char(
        "رقم الهاتف الاول",
        related="phone",
        readonly=False,
        store=True
    )

    second_phone_number = fields.Char(
        "رقم الهاتف الثاني ",
        related="mobile",
        readonly=False,
        store=True
    )


    email1 = fields.Char(
        "البريد الالكتروني",
        related="email",
        readonly=False,
        store=True
    )

    subscription_type = fields.Char(
        "نوع الاشتراك ",
        compute="_compute_subscription_type",
        inverse="_inverse_subscription_type",
        store=True
    )

    # subscription_type = fields.Char(
    #     "نوع الاشتراك (مرتبط بالتصنيفات)",
    #     compute="_compute_subscription_type",
    #     inverse="_inverse_subscription_type",
    #     store=True
    # )

    family_number = fields.Char("الرقم العائلي")


    @api.constrains('family_number')
    def _check_family_number_unique(self):
        """Check if username is unique"""
        for record in self:
            if record.family_number:
                existing = self.search([
                    ('family_number', '=', record.family_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f'اسم المستخدم "{record.user_name}" مستخدم بالفعل! يرجى اختيار اسم مستخدم آخر.')
    
    @api.constrains('user_name')
    def _check_user_name_unique(self):
        """Check if username is unique"""
        for record in self:
            if record.user_name:
                existing = self.search([
                    ('user_name', '=', record.user_name),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f'اسم المستخدم "{record.user_name}" مستخدم بالفعل! يرجى اختيار اسم مستخدم آخر.')
    
    
    # Add onchange to sync city with area_name_id
    @api.onchange('area_name_id')
    def _onchange_area_name_id(self):
        if self.area_name_id:
            self.city = self.area_name_id.name
            # Clear area_number_id when area changes
            self.area_number_id = False
    
    @api.onchange('city')
    def _onchange_city(self):
        # When city is changed manually, try to find matching area_name
        if self.city and not self.area_name_id:
            area = self.env['area.name'].search([('name', '=', self.city)], limit=1)
            if area:
                self.area_name_id = area.id
                
                
    
    @api.onchange('street2') 
    def _onchange_street2(self):
        if self.street2:
            self.nearest_point = self.street2
            
    
    
    

    
    @api.onchange('partner_longitude')
    def _onchange_partner_longitude(self):
        if self.partner_longitude:
            self.longitude_coordinates = self.partner_longitude

    @api.onchange('partner_latitude') 
    def _onchange_partner_latitude(self):
        if self.partner_latitude:
            self.latitude_coordinates = self.partner_latitude
    
    

    @api.depends('partner_latitude', 'partner_longitude')
    def _compute_google_maps_url(self):
        for record in self:
            if record.partner_latitude and record.partner_longitude:
                record.google_maps_url = f"https://www.google.com/maps?q={record.partner_latitude},{record.partner_longitude}"
            else:
                record.google_maps_url = False
                
    def action_open_google_maps(self):
        """Open Google Maps with the contact's location"""
        if not self.partner_latitude or not self.partner_longitude:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'خطأ!',
                    'message': 'لا توجد احداثيات للعميل',
                    'type': 'warning',
                }
            }
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.google_maps_url,
            'target': 'new',
        }
        
    def action_open_current_location_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "current.location.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_partner_id": self.id},
        }
    
   
    @api.onchange('ref')
    def _onchange_ref_port(self):
        if self.ref and self.ref.isdigit():
            self.port_number = int(self.ref)

    @api.onchange('name')
    def _onchange_name_full(self):
        if self.name:
            self.full_name_and_surname = self.name


    
    @api.onchange('phone')
    def _onchange_phone_first(self):
        if self.phone:
            self.first_phone_number = self.phone


    

    # Add onchange methods
    @api.onchange('mobile')
    def _onchange_mobile_second(self):
        if self.mobile:
            self.second_phone_number = self.mobile

    @api.onchange('email')
    def _onchange_email_first(self):
        if self.email:
            self.email1 = self.email

    # Compute methods for subscription_type
    @api.depends('category_id')
    def _compute_subscription_type(self):
        for record in self:
            if record.category_id:
                record.subscription_type = record.category_id[0].name
            else:
                record.subscription_type = ''

    def _inverse_subscription_type(self):
        for record in self:
            if record.subscription_type:
                # Find or create category
                category = self.env['res.partner.category'].search([
                    ('name', '=', record.subscription_type)
                ], limit=1)
                if not category:
                    category = self.env['res.partner.category'].create({
                        'name': record.subscription_type
                    })
                record.category_id = [(6, 0, [category.id])]
                
    def write(self, vals):
        """Override write to check username uniqueness"""
        if 'user_name' in vals and vals['user_name']:
            # Check if username is already taken
            existing = self.search([
                ('user_name', '=', vals['user_name']),
                ('id', 'not in', self.ids)
            ])
            if existing:
                raise ValidationError('اسم المستخدم "{}" مستخدم بالفعل! يرجى اختيار اسم مستخدم آخر.'.format(vals['user_name']))
        
        return super().write(vals)