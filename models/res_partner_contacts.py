from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Your existing fields...
    area_name_id = fields.Many2one(
        "area.name",
        'اسم المنطقة'
    )
    
    # Add area_number_id field
    area_number_id = fields.Many2one(
        "area.number",
        string="رقم المنطقة",
        domain="[('area_name_id', '=', area_name_id)]"  # Filter by selected area
    )
    
    # Related fields to sync with old module - these will sync with your old module's char fields
    area_name = fields.Char(
        "اسم المنطقة (للمزامنة مع الوحدة القديمة)",
        related="area_name_id.name",
        readonly=False,
        store=True
    )
    
    area_number = fields.Char(
        "رقم المنطقة (للمزامنة مع الوحدة القديمة)",
        related="area_number_id.name",
        readonly=False,
        store=True
    )
    
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
                
                
    nearest_point = fields.Char(
        "اقرب نقطة دالة (مرتبط بالشارع الثاني)",
        related="street2",
        readonly=False,
        store=True
    )
    @api.onchange('street2') 
    def _onchange_street2(self):
        if self.street2:
            self.nearest_point = self.street2
            
    
    
    longitude_coordinates = fields.Float(
        "احداثيات الطول (مرتبط بخط الطول)",
        related="partner_longitude",
        readonly=False,
        store=True,
        digits=(10, 6)
    )

    latitude_coordinates = fields.Float(
        "احداثيات العرض (مرتبط بخط العرض)", 
        related="partner_latitude",
        readonly=False,
        store=True,
        digits=(10, 6)
    )
    
    @api.onchange('partner_longitude')
    def _onchange_partner_longitude(self):
        if self.partner_longitude:
            self.longitude_coordinates = self.partner_longitude

    @api.onchange('partner_latitude') 
    def _onchange_partner_latitude(self):
        if self.partner_latitude:
            self.latitude_coordinates = self.partner_latitude
    
    google_maps_url = fields.Char(
        string="Google Maps URL",
        compute="_compute_google_maps_url"
    )

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