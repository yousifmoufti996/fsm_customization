from odoo import api, fields, models, _


class ProblemType(models.Model):
    _name = "problem.type"
    _description = "Problem Type"
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    name = fields.Char(string="نوع المشكلة",required=True,tracking=True)
    description = fields.Text(string="الوصف")
    
    
    estimated_duration = fields.Float(string='Estimated Duration (Hours)', default=1.0)
    
    @api.onchange('problem_type_id')
    def _onchange_problem_type_id(self):
        """تحديد المدة تلقائياً عند اختيار نوع المشكلة"""
        if self.problem_type_id:
            self.estimated_problem_duration = self.problem_type_id.estimated_duration
            # مسح الحل المختار عند تغيير نوع المشكلة
            self.problem_solution_id = False
        else:
            self.estimated_problem_duration = 0.0
    
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
            result.append((record.id, record.name))
        return result