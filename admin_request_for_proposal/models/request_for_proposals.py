# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date, datetime, timedelta, time
from odoo.exceptions import ValidationError


class AdminRequestForProposalLineProduct(models.Model):
    _name = 'admin.request.for.proposal.line.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Proposal"

    rfp_line_id = fields.Many2one('admin.request.for.proposal.line', string="RFP Line", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Product", track_visibility="always")
    product_name = fields.Char(string="Material/Service Name", track_visibility="always", required=True)
    name = fields.Text(string="Description")
    qty = fields.Float(string="Quantity", track_visibility="always")
    unit_name = fields.Char(string="Unit", track_visibility="always")
    price = fields.Float(string="Price", track_visibility="always")
    total = fields.Float(string="Subtotal", compute="_get_total", store=True)
    delivery_lead_time = fields.Float(string="Delivery Lead Time", help="In Days")
    validity_from = fields.Date(string="Valid From", track_visibility="always")
    validity_to = fields.Date(string="Valid To", track_visibility="always")
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')

    @api.depends('qty', 'price')
    def _get_total(self):
        for r in self:
            r.total = r.price * r.qty


class AdminRequestForProposalLine(models.Model):
    _name = 'admin.request.for.proposal.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Request for Proposal Line'
    _rec_name = 'partner_id'

    rfp_id = fields.Many2one('admin.request.for.proposals', string="RFI", ondelete="cascade")
    notes = fields.Html(string="Notes", track_visibility="always")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    proposal_line_ids = fields.One2many('admin.request.for.proposal.line.product', 'rfp_line_id')
    total = fields.Float(string="Grand Total", compute="_get_total", store=True)
    payment_terms = fields.Html(string="Payment Terms", track_visibility="always")
    other_term_warranty = fields.Html(string="Other Terms and Warranty", track_visibility="always")
    state = fields.Selection([('draft', 'Draft'),
                          ('selected_as_vendor', 'Selected as Vendor'),
                          ('done', 'Done'),
                          ('canceled', 'Cancelled')], string="Status",
                         default='draft', readonly=True, copy=False, track_visibility="always")

    def select_as_vendor(self):
        proposal_line_items = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id)])
        if not proposal_line_items:
            raise ValidationError("Please add a proposal item/s.")
        zero_product_price = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id), ('price', '<=', 0)])
        if zero_product_price:
            items = ""
            count = 1
            for item in zero_product_price:
                items += f"\n\t{count}. {item.product_name}"
                count += 1
            raise ValidationError(_(f"The price of the following item/s must be greater than zero: {items}"))
        self.state = 'selected_as_vendor'

    def cancel(self):
        self.state = 'canceled'

    def set_to_done(self):
        not_linked_products = self.env['admin.request.for.proposal.line.product'].sudo().search([('rfp_line_id', '=', self.id), ('product_id', '=', False)])
        if not_linked_products:
            items = ""
            count = 1
            for item in not_linked_products:
                items += f"\n\t{count}. {item.product_name}"
                count += 1
            raise ValidationError(_(f"Please link the following item/s to product: {items}"))
        for line in self.proposal_line_ids:
            vendor_pricelist = []
            create_update_pricelist = True
            if line.validity_from and line.validity_to:
                vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '>=', line.validity_from), ('date_end', '<=', line.validity_to), ('price', '=', line.price)])
                between_validity_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '<=', line.validity_from), ('date_end', '>=', line.validity_to), ('price', '=', line.price)])
                if between_validity_pricelist:
                    create_update_pricelist = False
            else:
                vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', line.product_id.id), ('name', '=', self.partner_id.id), ('date_start', '=', False), ('date_end', '=', False)])
            if create_update_pricelist:
                if vendor_pricelist:
                    for ln in vendor_pricelist:
                        ln.write({
                            'date_start': line.validity_from,
                            'date_end': line.validity_to,
                            'product_name': line.product_name,
                            'min_qty': line.qty,
                            'product_uom': line.product_id.uom_po_id.id,
                            'price': line.price,
                            'delay': line.delivery_lead_time,
                        })
                else:
                    self.env['product.supplierinfo'].sudo().create({
                        'product_tmpl_id': line.product_id.id,
                        'name': self.partner_id.id,
                        'date_start': line.validity_from,
                        'date_end': line.validity_to,
                        'product_name': line.product_name,
                        'min_qty': line.qty,
                        'product_uom': line.product_id.uom_po_id.id,
                        'price': line.price,
                        'delay': line.delivery_lead_time,
                    })
        self.state = 'done'

    @api.depends('proposal_line_ids', 'proposal_line_ids.qty', 'proposal_line_ids.price')
    def _get_total(self):
        for r in self:
            r.total = sum(i.total for i in r.proposal_line_ids)


class AdminRequestForProposals(models.Model):
    _name = 'admin.request.for.proposals'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'document.default.approval']
    _description = 'Request for Proposals'

    @api.model
    def default_get(self, default_fields):
        res = super(AdminRequestForProposals, self).default_get(default_fields)
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
    company_id = fields.Many2one('res.company', 'Company', required=True,
                        default=lambda self: self.env.company, track_visibility="always",
                        states={'draft': [('readonly', False)]}, readonly=True)
    user_id = fields.Many2one('res.users', string='Purchasing Officer', index=True, tracking=True, required=True,
                              default=lambda self: self.env.user, track_visibility="always", readonly=True,
                              states={'draft': [('readonly', False)]})
    create_date = fields.Datetime(string="Created Date", required=True, readonly=True, copy=False,
                                  default=fields.Datetime.now)
    est_del_date = fields.Date(string="Required Delivery Date", copy=False, readonly=True,
                               states={'draft': [('readonly', False)]},
                               help="Admin/Managers can set their estimated delivery date for this rfq, "
                                    "this information will be sent to the vendors.")
    due_date = fields.Date(string="Due Date", copy=False, readonly=True,
                           states={'draft': [('readonly', False)], 'pending': [('readonly', False)]})
    vendor_ids = fields.Many2many('res.partner', 'purchase_vendor_rfp_rel', string="Vendors", required=True,
                                  copy=False, states={'draft': [('readonly', False)]},
                                  help="Admin/Managers can add the vendors and invite for this RFI")
    attachment_ids = fields.Many2many('ir.attachment', 'rfp_mail_rel', string="Email Attachments", readonly=True,
                                      states={'draft': [('readonly', False)]})
    subject = fields.Char(string="Subject", required=True, track_visibility="always", readonly=True,
                          states={'draft': [('readonly', False)]})
    body_html = fields.Html(string="Email Body", required=True, tracking=True, track_visibility="always", readonly=True,
                            states={'draft': [('readonly', False)]})
    sent_rfp = fields.Boolean(string="RFP Sent")
    pr_related_ids = fields.Many2many('purchase.requisition.material.details', 'pr_rfp_rel', string='PR Related',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]})

    def submit_request(self):
        return self.write({
            'name': self.env['ir.sequence'].get('vendor.request.for.proposal'),
            'state': 'submitted',
            'submitted_by': self._uid,
            'submitted_date': datetime.now()
        })

    def send_rfp_email(self):
        for r in self.vendor_ids:
            res = self.env['admin.request.for.proposal.line'].sudo().create(
                {
                    'partner_id': r.id,
                    'rfp_id': self.id
                }
            )
            post_vars = {
                'partner_ids': [r.id],
                'attachment_ids': self.attachment_ids.ids
            }
            body = f"<p>Dear <b>{r.name}</b></p><br/> {self.body_html}"
            res.message_post(body=body, subject=self.subject, **post_vars)
        self.write({'sent_rfp': True})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Congratulation! '
                           f'Your RFP has been successfully sent to vendors',
                'type': 'rainbow_man',
            }
        }

    def set_to_done(self):
        selected_vendor = self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id', '=', self.id), ('state', '=', 'done')])
        if not selected_vendor:
            raise ValidationError("Please select/assign a vendor.")
        not_selected_vendor = self.env['admin.request.for.proposal.line'].sudo().search([('rfp_id', '=', self.id), ('state', '!=', 'done')])
        for line in not_selected_vendor:
            line.write({'state': 'canceled'})
        self.state = 'done'
