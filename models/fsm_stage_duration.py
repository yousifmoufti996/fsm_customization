from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError 


class FSMStageDuration(models.Model):
    _name = "fsm.stage.duration"
    _description = "FSM Order Stage Duration"
    _order = "sequence, id"

    order_id = fields.Many2one(
        "fsm.order",
        string="FSM Order",
        required=True,
        ondelete="cascade"
    )
    
    stage_id = fields.Many2one(
        "fsm.stage",
        string="Stage",
        required=True
    )
    
    start_date = fields.Datetime(
        string="Start Date",
        required=True
    )
    
    end_date = fields.Datetime(
        string="End Date"
    )
    
    duration = fields.Float(
        string="Duration (Hours)",
        compute="_compute_duration",
        store=True,
        help="Duration in hours"
    )
    duration_display = fields.Char(
        string="Duration",
        compute="_compute_duration_display",
        help="Duration in HH:MM:SS format"
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10
    )
    
    is_current = fields.Boolean(
        string="Current Stage",
        default=False
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0
                
    @api.depends('duration')
    def _compute_duration_display(self):
        for record in self:
            if record.duration:
                total_seconds = int(record.duration * 3600)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                record.duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                record.duration_display = "00:00:00"
                
    def write(self, vals):
        if ('start_date' in vals and len(vals['start_date']) !=0) or  ('end_date' in vals and len(vals['end_date']) !=0) or  ('duration' in vals and len(vals['duration']) !=0):
            raise ValidationError(_(
                "لا يمكن التعديل على المدة او وقت البداية او وقت النهاية"
            ))
        for record in self:
            if ('start_date' in vals and len(vals['start_date']) !=0) or  ('end_date' in vals and len(vals['end_date']) !=0) or  ('duration' in vals and len(vals['duration']) !=0):
                raise ValidationError(_(
                        "لا يمكن التعديل على المدة او وقت البداية او وقت النهاية"
                    ))