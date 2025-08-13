from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_category_id = fields.Many2one(
        'partner.category',
        string='Partner Category',
        help='Categorize partners (e.g., Blacklist, Whitelist, VIP, etc.)'
    )
    
    # Optional: Add a related field for easy access to category name
    partner_category_name = fields.Char(
        related='partner_category_id.name',
        string='Category Name',
        readonly=True,
        store=True
    )
    
    # Optional: Add a related field for category color
    partner_category_color = fields.Integer(
        related='partner_category_id.color',
        string='Category Color',
        readonly=True,
        store=True
    )
    
    is_partner_blacklisted = fields.Boolean(
        string="Blacklisted",
        default=False,
        help="If checked, this partner is blacklisted"
    )

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """Override search to add domain filters for categories"""
        # You can add custom search logic here if needed
        # For example, to exclude blacklisted partners by default in certain contexts
        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    def is_partner_blacklisted(self):
        """Helper method to check if partner is blacklisted"""
        blacklist_category = self.env['partner.category'].search([('code', '=', 'BLACKLIST')], limit=1)
        return self.partner_category_id == blacklist_category

    def is_whitelisted(self):
        """Helper method to check if partner is whitelisted"""
        whitelist_category = self.env['partner.category'].search([('code', '=', 'WHITELIST')], limit=1)
        return self.partner_category_id == whitelist_category

    def set_partner_blacklist(self):
        """Action to set partner as blacklisted"""
        blacklist_category = self.env['partner.category'].search([('code', '=', 'BLACKLIST')], limit=1)
        if blacklist_category:
            self.partner_category_id = blacklist_category.id

    def set_whitelist(self):
        """Action to set partner as whitelisted"""
        whitelist_category = self.env['partner.category'].search([('code', '=', 'WHITELIST')], limit=1)
        if whitelist_category:
            self.partner_category_id = whitelist_category.id

    def remove_category(self):
        """Action to remove category from partner"""
        self.partner_category_id = False