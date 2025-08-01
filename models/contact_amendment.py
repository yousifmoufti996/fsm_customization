# models/contact_amendment.py
from odoo import models, fields, api
from odoo.exceptions import UserError

# access_contact_amendment_user,contact.amendment.user,model_contact_amendment,fieldservice.group_fsm_user,1,1,1,0
# access_contact_amendment_manager,contact.amendment.manager,model_contact_amendment,fieldservice.group_fsm_manager,1,1,1,1
# access_contact_amendment_admin,contact.amendment.admin,model_contact_amendment,base.group_system,1,1,1,1
class ContactAmendment(models.Model):
    _name = 'contact.amendment'
    _description = 'Contact Information Amendment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Amendment Reference', required=True, copy=False, readonly=True, default='New')
    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Original Contact', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)

    # Proposed contact details
    proposed_name = fields.Char(string='Name')
    proposed_email = fields.Char(string='Email')
    proposed_phone = fields.Char(string='Phone')
    proposed_mobile = fields.Char(string='Mobile')
    proposed_website = fields.Char(string='Website')
    proposed_street = fields.Char(string='Street')
    proposed_street2 = fields.Char(string='Street 2')
    proposed_city = fields.Char(string='City')
    proposed_state_id = fields.Many2one('res.country.state', string='State')
    proposed_zip = fields.Char(string='ZIP')
    proposed_country_id = fields.Many2one('res.country', string='Country')
    proposed_vat = fields.Char(string='Tax ID')
    proposed_company_type = fields.Selection([
        ('person', 'Individual'),
        ('company', 'Company')
    ], string='Company Type', default='person')
    proposed_industry_id = fields.Many2one('res.partner.industry', string='Industry')
    proposed_function = fields.Char(string='Job Position')
    proposed_title = fields.Many2one('res.partner.title', string='Title')
    proposed_comment = fields.Text(string='Notes')
    proposed_ref = fields.Char(string='Internal Reference')
    proposed_lang = fields.Selection('_get_lang_selection', string='Language')
    # proposed_tz = fields.Selection('_tz_get', string='Timezone')
    proposed_is_company = fields.Boolean(string='Is a Company')

    # Approval fields
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')

    # Computed fields to show changes
    changes_summary = fields.Html(string='Changes Summary', compute='_compute_changes_summary')

    def _get_lang_selection(self):
        return self.env['res.lang'].get_installed()

    # def _tz_get(self):
    #     return [(x, x) for x in sorted(self.env['res.partner']._tz_get())]

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('contact.amendment') or 'New'
        return super().create(vals)

    @api.depends('partner_id', 'proposed_name', 'proposed_email', 'proposed_phone', 'proposed_mobile')
    def _compute_changes_summary(self):
        for record in self:
            if not record.partner_id:
                record.changes_summary = '<p>No original contact to compare</p>'
                continue
            
            changes = []
            partner = record.partner_id
            
            # Compare all fields and build changes list
            field_comparisons = [
                ('Name', partner.name, record.proposed_name),
                ('Email', partner.email, record.proposed_email),
                ('Phone', partner.phone, record.proposed_phone),
                ('Mobile', partner.mobile, record.proposed_mobile),
                ('Website', partner.website, record.proposed_website),
                ('Street', partner.street, record.proposed_street),
                ('City', partner.city, record.proposed_city),
                ('ZIP', partner.zip, record.proposed_zip),
                ('Tax ID', partner.vat, record.proposed_vat),
                ('Job Position', partner.function, record.proposed_function),
                ('Notes', partner.comment, record.proposed_comment),
            ]
            
            for field_name, original, proposed in field_comparisons:
                original = original or ''
                proposed = proposed or ''
                if original != proposed:
                    changes.append(f"<tr><td><strong>{field_name}</strong></td><td>{original}</td><td>{proposed}</td></tr>")
            
            if changes:
                record.changes_summary = f"""
                <table class="table table-sm">
                    <thead>
                        <tr><th>Field</th><th>Current</th><th>Proposed</th></tr>
                    </thead>
                    <tbody>
                        {''.join(changes)}
                    </tbody>
                </table>
                """
            else:
                record.changes_summary = '<p>No changes detected</p>'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Load partner data into proposed fields"""
        if self.partner_id:
            self.proposed_name = self.partner_id.name
            self.proposed_email = self.partner_id.email
            self.proposed_phone = self.partner_id.phone
            self.proposed_mobile = self.partner_id.mobile
            self.proposed_website = self.partner_id.website
            self.proposed_street = self.partner_id.street
            self.proposed_street2 = self.partner_id.street2
            self.proposed_city = self.partner_id.city
            self.proposed_state_id = self.partner_id.state_id
            self.proposed_zip = self.partner_id.zip
            self.proposed_country_id = self.partner_id.country_id
            self.proposed_vat = self.partner_id.vat
            self.proposed_company_type = self.partner_id.company_type
            self.proposed_industry_id = self.partner_id.industry_id
            self.proposed_function = self.partner_id.function
            self.proposed_title = self.partner_id.title
            self.proposed_comment = self.partner_id.comment
            self.proposed_ref = self.partner_id.ref
            self.proposed_lang = self.partner_id.lang
            # self.proposed_tz = self.partner_id.tz
            self.proposed_is_company = self.partner_id.is_company

    def action_submit_for_approval(self):
        """Submit amendment for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft amendments can be submitted for approval.")
        
        self.state = 'pending'
        self.message_post(body="Contact amendment submitted for approval.")

    def action_approve(self):
        """Approve and apply the amendment"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError("Only pending amendments can be approved.")

        # Update the partner
        update_vals = {
            'name': self.proposed_name,
            'email': self.proposed_email,
            'phone': self.proposed_phone,
            'mobile': self.proposed_mobile,
            'website': self.proposed_website,
            'street': self.proposed_street,
            'street2': self.proposed_street2,
            'city': self.proposed_city,
            'state_id': self.proposed_state_id.id if self.proposed_state_id else False,
            'zip': self.proposed_zip,
            'country_id': self.proposed_country_id.id if self.proposed_country_id else False,
            'vat': self.proposed_vat,
            'company_type': self.proposed_company_type,
            'industry_id': self.proposed_industry_id.id if self.proposed_industry_id else False,
            'function': self.proposed_function,
            'title': self.proposed_title.id if self.proposed_title else False,
            'comment': self.proposed_comment,
            'ref': self.proposed_ref,
            'lang': self.proposed_lang,
            # 'tz': self.proposed_tz,
            'is_company': self.proposed_is_company,
        }

        self.partner_id.write(update_vals)

        # Update amendment status
        self.state = 'approved'
        self.approved_by = self.env.user
        self.approved_date = fields.Datetime.now()
        
        self.message_post(body=f"Contact amendment approved and applied by {self.env.user.name}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Approved!',
                'message': 'Contact amendment has been approved and applied successfully.',
                'type': 'success',
            }
        }

    def action_reject(self):
        """Reject the amendment"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError("Only pending amendments can be rejected.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Amendment',
            'res_model': 'contact.amendment.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_amendment_id': self.id}
        }

    def action_reset_to_original(self):
        """Reset proposed fields to original partner values"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft amendments can be reset.")
        
        self._onchange_partner_id()
        self.message_post(body="Amendment reset to original contact values.")