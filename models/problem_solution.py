from odoo import api, fields, models, _


class ProblemSolution(models.Model):
    _name = "problem.solution"
    _description = "Problem Solution"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="الحل",
        required=True,
        tracking=True
    )
    description = fields.Text(
        string="وصف الحل"
    )
    problem_type_id = fields.Many2one(
        'problem.type',
        string="نوع المشكلة",
        required=True,
        ondelete='cascade'
    )
    active = fields.Boolean(
        default=True
    )
    sequence = fields.Integer(
        string="التسلسل",
        default=10
    )
    
    _order = 'problem_type_id, sequence, name'
    
    _sql_constraints = [
        ('name_problem_type_unique', 'unique(name, problem_type_id)', 
         'الحل يجب أن يكون فريداً لكل نوع مشكلة!')
    ]