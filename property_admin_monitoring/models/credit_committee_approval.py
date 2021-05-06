from odoo import fields, models, api, _


class PropertySaleCreditCommitteeApproval(models.Model):
    _name = 'property.sale.credit.committee.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Credit committee Approval'
    _rec_name = 'property_sale_id'

    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale", track_visibility="always",
                                       readonly=True)
    so_number = fields.Char(string="SO Number", related="property_sale_id.so_number", store=True)
    so_date = fields.Date(string="SO Date", related="property_sale_id.so_date", store=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related="property_sale_id.partner_id", store=True)
    company_id = fields.Many2one('res.company', string='Company', related="property_sale_id.company_id", store=True)
    subdivision_phase_id = fields.Many2one('property.subdivision.phase', string="Project",
                                           related="property_sale_id.subdivision_phase_id", store=True)
    brand = fields.Char(string="Brand", related="subdivision_phase_id.brand", store=True)
    block_lot = fields.Char(string="Block-Lot", related="property_sale_id.block_lot", store=True)

    note = fields.Text(string="Notes", track_visibility="always", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                               ('waiting for verification', 'Waiting for Verification'),
                               ('waiting for approval', 'Waiting for Approval'),
                               ('approved', 'Approved'),
                               ('rejected', 'Rejected')], string="Status", default='draft', track_visibility="always")
    submitted_by = fields.Many2one('res.users', string="Submitted By", track_visibility="always")
    submitted_date = fields.Datetime(string="Submitted Time", track_visibility="always")
    verified_by = fields.Many2one('res.users', string="Verified By", track_visibility="always")
    verified_date = fields.Datetime(string="Verified Time", track_visibility="always")
    approved_by = fields.Many2one('res.users', string="Approved By", track_visibility="always")
    approved_date = fields.Datetime(string="Approved Time", track_visibility="always")
    rejected_by = fields.Many2one('res.users', string="Rejected By", track_visibility="always")
    rejected_date = fields.Datetime(string="Rejected Time", track_visibility="always")
    rejecting_reason_id = fields.Many2one('property.sale.cancellation.reason', string="Rejecting Reason",
                                          track_visibility="always")
    rejecting_notes = fields.Text(string="Rejecting Notes", track_visibility="always")

    def write(self, vals):
        super(PropertySaleCreditCommitteeApproval, self).write(vals)
        if vals.get('rejecting_reason_id'):
            email_temp = self.env.ref('property_admin_monitoring.email_template_rejected_credit_committee_approval')
            self.message_post_with_template(email_temp.id)
        return True

    def request_submit(self):
        return self.write({
            'submitted_by': self._uid,
            'submitted_date': fields.datetime.now(),
            'state': 'waiting for verification'
        })

    def request_verify(self):
        return self.write({
            'verified_by': self._uid,
            'verified_date': fields.datetime.now(),
            'state': 'waiting for approval'
        })

    def request_approve(self):
        return self.write({
            'approved_by': self._uid,
            'approved_date': fields.datetime.now(),
            'state': 'approved'
        })

    def request_reset_to_draft(self):
        return self.write({
            'state': 'draft'
        })
