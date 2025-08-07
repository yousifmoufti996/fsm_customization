from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    stage_duration_ids = fields.One2many(
        "fsm.stage.duration",
        "order_id",
        string="Stage Durations"
    )
    
    total_stage_duration = fields.Float(
        string="Total Duration (Hours)",
        compute="_compute_total_stage_duration",
        help="Total time spent across all stages"
        , digits=(16, 4)
    )
    
    total_duration_display = fields.Char(
        string="Total Duration",
        compute="_compute_total_duration_display",
        help="Total duration in HH:MM:SS format"
    )
    
    
    creation_to_work_done_duration = fields.Float(
        string="Creation to Work Done (Hours)",
        compute="_compute_creation_to_work_done_duration",
        help="Duration from order creation to تم العمل stage", digits=(16, 4)
    )
    
    creation_to_work_done_display = fields.Char(
        string="مدة من انشاء التكت لغاية تم العمل",
        compute="_compute_creation_to_work_done_display",
        help="Duration from ticket creation to تم العمل stage in HH:MM:SS format",
        store=True,
    )
    
    in_way_to_work_progress_duration = fields.Float(
        string="In Way to Work Progress (Hours)",
        compute="_compute_in_way_to_work_progress_duration",
        help="Duration from in the way to work in progress", digits=(16, 4)
    )
    
    in_way_to_work_progress_display = fields.Char(
        string="مدة من وقت بدأ في الطريق الى وقت بدأ جاري العمل",
        compute="_compute_in_way_to_work_progress_display",
        help="Duration from in the way to work in progress in HH:MM:SS format"
    )
    work_progress_to_done_duration = fields.Float(
        string="Work Progress to Done (Hours)",
        compute="_compute_work_progress_to_done_duration",
        help="Duration from work in progress to work done", digits=(16, 4)
    )
    work_progress_to_done_display = fields.Char(
        string="مدة من جاري العمل الى تم العمل",
        compute="_compute_work_progress_to_done_display",
        help="Duration from work in progress to work done in HH:MM:SS format"
    )
    
    combined_way_work_duration = fields.Float(
        string="Combined Way and Work (Hours)",
        compute="_compute_combined_way_work_duration",
        help="Combined duration of في الطريق + جاري العمل", digits=(16, 4)
    )
    
    combined_way_work_display = fields.Char(
        string="مجموع مدة (في الطريق + جاري العمل)",
        compute="_compute_combined_way_work_display",
        help="Combined duration of في الطريق + جاري العمل in HH:MM:SS format"
    )
    
    full_duration = fields.Float(
        string="Full Duration (Hours)",
        compute="_compute_full_duration",
        help="Duration from creation to any closed stage", digits=(16, 4)
    )
    
    full_duration_display = fields.Char(
        string="المدة الكاملة من الانشاء للاغلاق",
        compute="_compute_full_duration_display",
        help="Duration from creation to any closed stage in HH:MM:SS format"
    )
    
    

    @api.depends('stage_duration_ids.duration')
    def _compute_total_stage_duration(self):
        for order in self:
            order.total_stage_duration = sum(order.stage_duration_ids.mapped('duration'))

    
    def _format_duration_to_hhmmss(self, duration_hours):
        """Convert duration in hours to HH:MM:SS format"""
        if duration_hours:
            total_seconds = int(duration_hours * 3600)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return "00:00:00"
        
    
    @api.depends('total_stage_duration')
    def _compute_total_duration_display(self):
        for order in self:
            order.total_duration_display = order._format_duration_to_hhmmss(order.total_stage_duration)


    @api.depends('create_date', 'stage_duration_ids')
    def _compute_creation_to_work_done_duration(self):
        for order in self:
            # Find "تم العمل" stage start time
            work_done_stage = order.stage_duration_ids.filtered(lambda x: x.stage_id.name == 'تم العمل')
            
            if order.create_date and work_done_stage:
                work_done_start = min(work_done_stage.mapped('start_date'))
                delta = work_done_start - order.create_date
                order.creation_to_work_done_duration = delta.total_seconds() / 3600
            else:
                order.creation_to_work_done_duration = 0.0

    @api.depends('creation_to_work_done_duration')
    def _compute_creation_to_work_done_display(self):
        for order in self:
            order.creation_to_work_done_display = order._format_duration_to_hhmmss(order.creation_to_work_done_duration)
            
            
    @api.depends('stage_duration_ids')
    def _compute_in_way_to_work_progress_duration(self):
        for order in self:
            # Find "في الطريق" and "جاري العمل" stages
            in_way_stage = order.stage_duration_ids.filtered(lambda x: x.stage_id.name == 'في الطريق')
            work_progress_stage = order.stage_duration_ids.filtered(lambda x: x.stage_id.name == 'جاري العمل')
            
            if in_way_stage and work_progress_stage:
                # Get the earliest in_way and earliest work_progress
                in_way_start = min(in_way_stage.mapped('start_date'))
                work_progress_start = min(work_progress_stage.mapped('start_date'))
                
                if in_way_start and work_progress_start:
                    delta = work_progress_start - in_way_start
                    order.in_way_to_work_progress_duration = delta.total_seconds() / 3600
                else:
                    order.in_way_to_work_progress_duration = 0.0
            else:
                order.in_way_to_work_progress_duration = 0.0

    @api.depends('in_way_to_work_progress_duration')
    def _compute_in_way_to_work_progress_display(self):
        for order in self:
            order.in_way_to_work_progress_display = order._format_duration_to_hhmmss(order.in_way_to_work_progress_duration)

    
    @api.depends('stage_duration_ids')
    def _compute_work_progress_to_done_duration(self):
        for order in self:
            # Find "جاري العمل" and "تم العمل" stages
            work_progress_stage = order.stage_duration_ids.filtered(lambda x: x.stage_id.name == 'جاري العمل')
            work_done_stage = order.stage_duration_ids.filtered(lambda x: x.stage_id.name == 'تم العمل')
            
            if work_progress_stage and work_done_stage:
                # Get the earliest work_progress and earliest work_done
                work_progress_start = min(work_progress_stage.mapped('start_date'))
                work_done_start = min(work_done_stage.mapped('start_date'))
                
                if work_progress_start and work_done_start:
                    delta = work_done_start - work_progress_start
                    order.work_progress_to_done_duration = delta.total_seconds() / 3600
                else:
                    order.work_progress_to_done_duration = 0.0
            else:
                order.work_progress_to_done_duration = 0.0

    @api.depends('work_progress_to_done_duration')
    def _compute_work_progress_to_done_display(self):
        for order in self:
            order.work_progress_to_done_display = order._format_duration_to_hhmmss(order.work_progress_to_done_duration)

    
    @api.depends('in_way_to_work_progress_duration', 'work_progress_to_done_duration')
    def _compute_combined_way_work_duration(self):
        for order in self:
            order.combined_way_work_duration = order.in_way_to_work_progress_duration + order.work_progress_to_done_duration

    @api.depends('combined_way_work_duration')
    def _compute_combined_way_work_display(self):
        for order in self:
            order.combined_way_work_display = order._format_duration_to_hhmmss(order.combined_way_work_duration)

    @api.depends('create_date', 'stage_duration_ids')
    def _compute_full_duration(self):
        for order in self:
            # Find any closed stage
            closed_stages = order.stage_duration_ids.filtered(lambda x: x.stage_id.is_closed)
            
            if order.create_date and closed_stages:
                closed_start = min(closed_stages.mapped('start_date'))
                delta = closed_start - order.create_date
                order.full_duration = delta.total_seconds() / 3600
            else:
                order.full_duration = 0.0

    @api.depends('full_duration')
    def _compute_full_duration_display(self):
        for order in self:
            order.full_duration_display = order._format_duration_to_hhmmss(order.full_duration)


    
    

    def _track_stage_change(self, order, new_stage_id):
        """Track when stage changes to record duration"""
        now = fields.Datetime.now()
        
        # End current stage if exists
        # current_stage_duration = order.stage_duration_ids.filtered('is_current')
        # if current_stage_duration:
        #     current_stage_duration.write({
        #         'end_date': now,
        #         # 'is_current': False
        #     })
        
        # Start new stage
        new_stage = self.env['fsm.stage'].browse(new_stage_id)
        self.env['fsm.stage.duration'].create({
            'order_id': order.id,
            'stage_id': new_stage_id,
            'start_date': now,
            # 'is_current': True,
            'sequence': len(order.stage_duration_ids) + 1
        })

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        # Track initial stage for new orders
        for order in orders:
            if order.stage_id:
                self.env['fsm.stage.duration'].create({
                    'order_id': order.id,
                    'stage_id': order.stage_id.id,
                    'start_date': fields.Datetime.now(),
                    # 'is_current': True,
                    'sequence': 1
                })
        return orders