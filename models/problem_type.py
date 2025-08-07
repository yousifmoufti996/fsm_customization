from odoo import api, fields, models, _


class ProblemType(models.Model):
    _name = "problem.type"
    _description = "Problem Type"
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    name = fields.Char(string="نوع المشكلة",required=True,tracking=True)
    description = fields.Text(string="الوصف")
    
    
    estimated_duration = fields.Float(
        string='Estimated Duration (Hours)', 
        default=1.0,
        tracking=True, digits=(16, 4)
    )
    
    estimated_duration_display = fields.Char(
        string='Duration (HH:MM:SS)', 
        compute='_compute_duration_display',
        inverse='_inverse_duration_display',
        store=False  # Don't store in database, calculate on-the-fly
    )

    @api.depends('estimated_duration')
    def _compute_duration_display(self):
        for record in self:
            if record.estimated_duration:
                total_seconds = int(record.estimated_duration * 3600)  # Convert hours to seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                record.estimated_duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                record.estimated_duration_display = "00:00:00"
                
    def _inverse_duration_display(self):
        for record in self:
            if record.estimated_duration_display:
                try:
                    # Parse HH:MM:SS format
                    time_parts = record.estimated_duration_display.split(':')
                    if len(time_parts) == 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        seconds = int(time_parts[2])
                        # Convert to hours (float)
                        record.estimated_duration = hours + (minutes / 60.0) + (seconds / 3600.0)
                    elif len(time_parts) == 2:  # HH:MM format
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        record.estimated_duration = hours + (minutes / 60.0)
                    else:
                        record.estimated_duration = 0.0
                except (ValueError, IndexError):
                    record.estimated_duration = 0.0
    
    solution_ids = fields.One2many(
        'problem.solution', 
        'problem_type_id', 
        string="الحلول المتاحة"
    )
    active = fields.Boolean(
        default=True
    )
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} (Duration: {record.estimated_duration}h)"
            result.append((record.id, name))
        return result