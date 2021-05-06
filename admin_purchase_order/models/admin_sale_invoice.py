# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger("_name_")


class AdminInvoicePayment(models.Model):
    _name = 'admin.invoice.payment'
    _description = "SI Payment Documents"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_release_date desc'

    name = fields.Char(string="Payment Transaction No.", required=True, track_visibility="always", copy=False, index=True)
    payment_release_date = fields.Date(string="Payment Date", required=True, track_visibility="always")
    amount = fields.Float(string="Amount", required=True, track_visibility="always")
    or_number = fields.Char(string="OR Number", track_visibility="always")
    original_or_received = fields.Boolean(string="Original OR Received", track_visibility="always")
    original_or_received_date = fields.Date(string="Original OR Received Date", track_visibility="always")
    remark = fields.Text(string="Remarks", track_visibility="always")
    admin_si_id = fields.Many2one('admin.sales.invoice', string="Sales Invoice", track_visibility="always",
                                  domain="[('company_id', '=', company_id), ('vendor_partner_id', '=', vendor_partner_id)]")
    invoice_date = fields.Date(string="Invoice Date", store=True, related="admin_si_id.invoice_date")
    si_amount = fields.Float('SI Amount', store=True, related="admin_si_id.amount")
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", store=True, related="admin_si_id.purchase_id")
    vendor_partner_id = fields.Many2one('res.partner', string="Supplier/Vendor", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=True, required=True)

    # @api.onchange('admin_si_id')
    # def onchange_admin_si(self):
    #     if self.admin_si_id:
    #         self.purchase_id = self.admin_si_id.purchase_id and self.admin_si_id.purchase_id.id or False

    def check_amount_against_invoice(self, invoice_id, amount):
        r = self.env['admin.sales.invoice'].sudo().browse(invoice_id)
        inv_amount = r.amount
        payments = self.sudo().search([('admin_si_id', '=', invoice_id), ('id', 'not in', [self.id])])
        if inv_amount < (amount + sum([r.amount for r in payments])):
            raise ValidationError(_("You are releasing total (Current + Previous) payment greater than the Invoice Value"))

    @api.model
    def create(self, vals):
        if vals.get('admin_si_id'):
            self.check_amount_against_invoice(vals.get('admin_si_id'), vals.get('amount'))
        res = super(AdminInvoicePayment, self).create(vals)
        return res

    def write(self, vals):
        if (vals.get('admin_si_id') or self.admin_si_id) or (vals.get('amount') or self.amount):
            self.check_amount_against_invoice(vals.get('admin_si_id') or self.admin_si_id.id, vals.get('amount') or self.amount)
        super(AdminInvoicePayment, self).write(vals)
        return True


class AdminSalesInvoice(models.Model):
    _name = 'admin.sales.invoice'
    _description = 'Admin Sales Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vendor_si_number'
    _order = 'invoice_date desc'

    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", track_visibility="always", domain="[('company_id', '=', company_id), ('partner_id', '=', vendor_partner_id)]")
    service_order_number = fields.Char(string="Service Order Number", track_visibility="always")
    admin_si_type = fields.Selection([('with_po', 'PO Related'), ('no_po', 'None PO Related')], string="Document Type",
                                     required=True, track_visibility="always")
    vendor_partner_id = fields.Many2one('res.partner', string="Supplier/Vendor", required=True)
    vendor_si_number = fields.Char(string="Vendor SI Number", required=True, track_visibility="always", copy=False,
                                   index=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, track_visibility="always")
    amount = fields.Float(string="Amount", track_visibility="always")
    invoice_date = fields.Date(string="Date", track_visibility="always")
    vendor_remarks = fields.Text(string="Vendor Remarks", track_visibility="always")
    po_delivery_ids = fields.Many2many('po.delivery.line', 'admin_si_delivery_rel', string="Delivery Document")
    countered = fields.Boolean(string="Countered")
    countered_date = fields.Date(string="Countered Date")
    vendor_payment_count = fields.Integer(compute="_compute_vendor_payment_count")

    def _compute_vendor_payment_count(self):
        for r in self:
            r.vendor_payment_count = self.env['admin.invoice.payment'].sudo().search_count([('admin_si_id', '=', r.id)])

    def action_open_admin_si_payment(self):
        self.ensure_one()
        return {
            'name': _('Payment Released'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot',
            'res_model': 'admin.invoice.payment',
            'domain': [('admin_si_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_admin_si_id': self.id,
                'default_vendor_partner_id': self.vendor_partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    @api.onchange('countered')
    def onchange_countered(self):
        if self.countered:
            self.check_countering()
            self.countered_date = date.today()
        else:
            self.countered_date = False

    @api.constrains('po_delivery_ids', 'countered', 'countered_date')
    def check_countering(self):
        if len(self.po_delivery_ids.ids) > 0:
            if any([self.countered, self.countered_date]):
                for dr in self.po_delivery_ids:
                    if not dr.countered:
                        raise ValidationError(_(
                            "Please make sure that all DR/GR related to this SI has been tagged as Countered, before tagging this SI as Countered"))

    def check_amount_against_invoice(self, purchase_id, amount):
        r = self.env['purchase.order'].sudo().browse(purchase_id)
        po = r.amount_total
        invoice = self.sudo().search([('purchase_id', '=', purchase_id), ('id', 'not in', [self.id])])
        if po < (amount + sum([r.amount for r in invoice])):
            raise ValidationError(_("Your total (Current + Previous) SI Value is greater than the POValue"))

    @api.model
    def create(self, vals):
        if vals.get('purchase_id'):
            self.check_amount_against_invoice(vals.get('purchase_id'), vals.get('amount'))
        res = super(AdminSalesInvoice, self).create(vals)
        return res

    def write(self, vals):
        if (vals.get('purchase_id') or self.purchase_id) or (vals.get('amount') or self.amount):
            self.check_amount_against_invoice(vals.get('purchase_id') or self.purchase_id.id, vals.get('amount') or self.amount)
        super(AdminSalesInvoice, self).write(vals)
        return True
