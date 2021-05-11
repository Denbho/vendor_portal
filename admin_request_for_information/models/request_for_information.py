# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, date, timedelta


class AdminRequestForInformationLine(models.Model):
    _name = 'admin.request.for.information.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Request for product information'
    _rec_name = 'partner_id'

    rfi_id = fields.Many2one('admin.request.for.information', string="RFI", ondelete="cascade")
    notes = fields.Html(string="Notes")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)


class AdminRequestForInformation(models.Model):
    _name = 'admin.request.for.information'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'document.default.approval']
    _description = 'Request for product information'

    @api.model
    def default_get(self, default_fields):
        res = super(AdminRequestForInformation, self).default_get(default_fields)
        body = '<div style="margin:0px;padding: 0px;">' \
               '<p style="padding: 0px; font-size: 13px;">' \
               '--Your Email Body Here.<br><br><span class="fontstyle0">Regards.' \
               '<br>Vistaland Purchasing Team</span> </p></div>'
        res.update({
            'body_html': body
        })
        return res

    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Waiting for Confirmation'),
                              ('confirmed', 'Waiting for Verification'),
                              ('verified', 'Waiting for Approval'),
                              ('approved', 'Approved'),
                              ('done', 'Done'),
                              ('canceled', 'Cancelled')], string="Status",
                             default='draft', readonly=True, copy=False, track_visibility="always")
    name = fields.Char('Request Reference', copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                        default=lambda self: self.env.company, track_visibility="always",
                        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Purchasing Officer', index=True, tracking=True, required=True,
                              default=lambda self: self.env.user, track_visibility="always", readonly=True,
                              states={'draft': [('readonly', False)]})
    create_date = fields.Datetime(string="Created Date", required=True, readonly=True, copy=False,
                                  default=fields.Datetime.now)
    due_date = fields.Date(string="Due Date", copy=False, readonly=True,
                           states={'draft': [('readonly', False)], 'pending': [('readonly', False)]})
    vendor_ids = fields.Many2many('res.partner', 'purchase_vendor_rfi_rel', string="Vendors", required=True,
                                  copy=False, states={'draft': [('readonly', False)]},
                                  help="Admin/Managers can add the vendors and invite for this RFI")
    attachment_ids = fields.Many2many('ir.attachment', 'rfi_mail_rel', string="Email Attachments", readonly=True,
                                      states={'draft': [('readonly', False)]})
    subject = fields.Char(string="Subject", required=True, track_visibility="always", readonly=True,
                          states={'draft': [('readonly', False)]})
    body_html = fields.Html(string="Email Body", required=True, tracking=True, track_visibility="always", readonly=True,
                            states={'draft': [('readonly', False)]})
    sent_rfi = fields.Boolean(string="RFI Sent")

    def submit_request(self):
        return self.write({
            'name': self.env['ir.sequence'].get('vendor.request.for.information'),
            'state': 'submitted',
            'submitted_by': self._uid,
            'submitted_date': datetime.now()
        })

    def send_rfi_email(self):
        for r in self.vendor_ids:
            res = self.env['admin.request.for.information.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfi_id': self.id
                }
            )
            post_vars = {
                'partner_ids': [r.id],
                'attachment_ids': self.attachment_ids.ids
            }
            body = f"<p>Dear <b>{r.name}</b></p><br/> {self.body_html}"
            res.message_post(body=body, subject=self.subject, **post_vars)
        self.write({'sent_rfi': True})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Congratulation! '
                           f'Your RFI has been successfully sent to vendors',
                'type': 'rainbow_man',
            }
        }
