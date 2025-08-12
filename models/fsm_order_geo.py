from odoo import fields, models,api

class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    
    phone1 = fields.Char(related='customer_id.phone', store=True)
    mobile1 = fields.Char(related='customer_id.mobile', store=True)
    street1 = fields.Char(related='customer_id.street', store=True)
    street21 = fields.Char(related='customer_id.street2', store=True)
    city1 = fields.Char(related='customer_id.city', store=True)
    zip1 = fields.Char(related='customer_id.zip', store=True)
    state_name1 = fields.Char(related='customer_id.state_id.name', store=True)
    country_name1 = fields.Char(related='customer_id.country_id.name', store=True)
    latitude1 = fields.Float('Latitude',related='customer_id.partner_latitude', digits=(10, 6))
    longitude1 = fields.Float('Longitude',related='customer_id.partner_longitude', digits=(10, 6))
    print('oooooooooooooooooooooooooooooooooooooooooo')
    print('longitude')
    # print(longitude1)
    # print('latitude')
    # print(latitude1)
    
    # print('customer_id.partner_longitude')
    # print(self.customer_id.partner_longitude)
    # print('latitude')
    # print(latitude)
    
     # Main fields (the ones GeoEngine or the base view uses)
    phone = fields.Char()
    mobile = fields.Char()
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    state_name = fields.Char()
    country_name = fields.Char()
    latitude = fields.Float()
    longitude = fields.Float()

    @api.depends(
        'phone1', 'mobile1', 'street1', 'street21', 
        'city1', 'zip1', 'state_name1', 'country_name1'
    )
    def _sync_main_fields(self):
        """Sync *_1 fields into main fields."""
    
        for rec in self:
            print("rec.longitude")
            print(rec.longitude)
            print('rec.latitude')
            print(rec.latitude)
            rec.phone = rec.phone1
            rec.mobile = rec.mobile1
            rec.street = rec.street1
            rec.street2 = rec.street21
            rec.city = rec.city1
            rec.zip = rec.zip1
            rec.state_name = rec.state_name1
            rec.country_name = rec.country_name1
            rec.latitude = rec.latitude1
            rec.longitude = rec.longitude1

    # Make them computed+stored so they stay in DB and sync automatically
    phone = fields.Char(compute="_sync_main_fields", store=True)
    mobile = fields.Char(compute="_sync_main_fields", store=True)
    street = fields.Char(compute="_sync_main_fields", store=True)
    street2 = fields.Char(compute="_sync_main_fields", store=True)
    city = fields.Char(compute="_sync_main_fields", store=True)
    zip = fields.Char(compute="_sync_main_fields", store=True)
    state_name = fields.Char(compute="_sync_main_fields", store=True)
    country_name = fields.Char(compute="_sync_main_fields", store=True)
    latitude = fields.Char(compute="_sync_main_fields", store=True)
    longitude = fields.Char(compute="_sync_main_fields", store=True)
            
            
    # phone55 = fields.Char(related='customer_id.phone', store=True)
    
    # DO NOT redefine stage_name if it already exists in fieldservice
