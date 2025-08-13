from odoo import fields, models


class PartnerCategory(models.Model):
    _name = "partner.category"
    _description = "Partner Category"
    _order = "name"

    name = fields.Char(string="Category Name", required=True, translate=True)
    description = fields.Text(string="Description")
    color = fields.Integer(string="Color Index", default=0)
    active = fields.Boolean(string="Active", default=True)
    
    # Optional: Add a sequence field for ordering
    sequence = fields.Integer(string="Sequence", default=10)
    
    # Optional: Add a code field for easy identification
    code = fields.Char(string="Category Code", size=10)
    
    # Computed field to count partners in this category
    partner_count = fields.Integer(
        string="Number of Partners",
        compute="_compute_partner_count"
    )

    def _compute_partner_count(self):
        """Compute the number of partners in each category"""
        for category in self:
            category.partner_count = self.env['res.partner'].search_count([
                ('partner_category_id', '=', category.id)
            ])

    def action_view_partners(self):
        """Action to view partners in this category"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Partners in {self.name}',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('partner_category_id', '=', self.id)],
            'context': {'default_partner_category_id': self.id}
        }

    def name_get(self):
        """Override name_get to show code and name if code exists"""
        result = []
        for record in self:
            if record.code:
                name = f"[{record.code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Category code must be unique!'),
        ('name_unique', 'unique(name)', 'Category name must be unique!'),
    ]