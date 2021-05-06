# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning
import re

_SAP_DELIVERY_STATUS = [
    ('undelivered', 'Undelivered'),
    ('partially_delivered', 'Partially Delivered'),
    ('fully_delivered', 'Fully Delivered'),
]


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sap_delivery_status = fields.Selection(selection=_SAP_DELIVERY_STATUS, string='SAP Delivery Status')
    delivery_line = fields.One2many('po.delivery.line', 'po_id', string='Delivery Information')
    invoice_payment_line = fields.One2many('po.invoices.and.payments', 'po_id', string='Invoices and Payments')
    delivery_count = fields.Integer(compute="_compute_dr_count")
    vendor_si_count = fields.Integer(compute="_compute_vendor_si_count")
    vendor_payment_count = fields.Integer(compute="_compute_vendor_payment_count")

    def _compute_vendor_payment_count(self):
        for r in self:
            r.vendor_payment_count = self.env['admin.invoice.payment'].sudo().search_count([('purchase_id', '=', r.id)])

    def _compute_dr_count(self):
        for r in self:
            r.delivery_count = self.env['po.delivery.line'].sudo().search_count([('po_id', '=', r.id)])

    def _compute_vendor_si_count(self):
        for r in self:
            r.vendor_si_count = self.env['admin.sales.invoice'].sudo().search_count([('purchase_id', '=', r.id)])

    def action_open_admin_sale_invoice(self):
        self.ensure_one()
        return {
            'name': _('Sales Invoice'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'admin.sales.invoice',
            'domain': [('purchase_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_purchase_id': self.id,
                'default_admin_si_type': 'with_po',
                'default_vendor_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def action_open_admin_po_payment(self):
        self.ensure_one()
        return {
            'name': _('Payment Released'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'admin.invoice.payment',
            'domain': [('purchase_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_vendor_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id,
            },
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sap_goods_receipt = fields.Integer(string="SAP Goods Receipt")
    sap_delivery_status = fields.Selection(selection=_SAP_DELIVERY_STATUS, string='SAP Delivery Status')
    delivery_product_line = fields.One2many('po.delivery.product.line', 'product_line_id',
                                            string='Delivery Product Line')
    si_product_line = fields.One2many('po.invoices.and.payments.product.line', 'product_line_id',
                                      string='SI Product Line')
    pr_references = fields.Char(string="Purchase Requisition References")
    qty_delivered = fields.Float(string="Delivered Qty", store=True, compute="_compute_qty_received")
    pr_references = fields.Char(string="PR References")
    pr_notes = fields.Text(string="PR Notes")
    purchase_requisition_line_ids = fields.Many2many('purchase.requisition.material.details', 'po_pr_line_rel')

    @api.onchange('pr_references')
    def onchange_pr_reference(self):
        if self.pr_references:
            pr = re.split('; |, |\*|\n', self.pr_references)
            if pr:
                pr_rec = self.env['purchase.requisition.material.details'].sudo().search([
                    ('request_id.name', 'in', pr),
                    ('request_id.company_id', '=', self.company_id.id),
                    ('material_code', '=', self.product_id.default_code)
                ])
                self.purchase_requisition_line_ids = [(6, 0, pr_rec.ids)]

    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        res.onchange_pr_reference()
        return res

    def write(self, vals):
        super(PurchaseOrderLine, self).write(vals)
        if vals.get('pr_references') or vals.get('company_id'):
            self.onchange_pr_reference()
        return True


    @api.depends('delivery_product_line', 'delivery_product_line.delivery_quantity')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            line.qty_received = 0.0
            line.qty_delivered = 0.0
            total = 0
            for delivery in line.delivery_product_line:
                total += delivery.delivery_quantity
            if total > 0:
                line.qty_received = total
                line.qty_delivered = total

    @api.depends('name', 'product_qty')
    def name_get(self):
        result = []
        for po_line in self:
            name = po_line.name
            if self.env.context.get('show_product_qty'):
                name += ' (' + str(po_line.product_qty) + ')'
            if self.env.context.get('show_price'):
                name += ' (' + "{:,.2f}".format(po_line.price_unit) + ')'
            result.append((po_line.id, name))
        return result


class PODeliveryLine(models.Model):
    _name = "po.delivery.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "PO Delivery Line"
    _rec_name = "dr_no"

    dr_no = fields.Char('DR No.')
    gr_number = fields.Char('GR No.')
    dr_date = fields.Date('DR Date')
    receiving_date = fields.Date('Receiving Date')
    delivered_by = fields.Char(string="Delivered By")
    received_by = fields.Char(string="Received By")
    company_id = fields.Many2one('res.company', string="Company", store=True, related="po_id.company_id")
    po_id = fields.Many2one('purchase.order', string='PO #')
    product_line = fields.One2many('po.delivery.product.line', 'po_delivery_id', string='Product Lines')
    received_original_doc = fields.Boolean(string="Received Original Docs")
    received_original_doc_date = fields.Date(string="Received Original Docs Date")
    countered = fields.Boolean(string="Countered")
    countered_date = fields.Date(string="Countered Date")

    @api.onchange('received_original_doc')
    def onchange_received_original_doc(self):
        if self.received_original_doc:
            self.received_original_doc_date = date.today()
        else:
            self.received_original_doc_date = False

    @api.onchange('countered')
    def onchange_countered(self):
        if self.countered:
            self.countered_date = date.today()
        else:
            self.countered_date = False


class PODeliveryProductLine(models.Model):
    _name = "po.delivery.product.line"
    _description = "PO Delivery Product Line"

    name = fields.Char(string="Description")
    po_delivery_id = fields.Many2one('po.delivery.line', string='DR No.')
    po_id = fields.Many2one('purchase.order', string='PO No.')
    product_line_id = fields.Many2one('purchase.order.line', string='Product', required=True)
    product_id = fields.Many2one('product.product', string="Material/Service", store=True, related="product_line_id.product_id")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', store=True, related="product_line_id.product_uom")
    product_uom_category_id = fields.Many2one(store=True, related='product_line_id.product_id.uom_id.category_id')
    delivery_quantity = fields.Float(string='Delivery Quantity')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.onchange('product_line_id')
    def _onchange_product_line_id(self):
        self.name = self.product_line_id.name
        self.delivery_quantity = self.product_line_id.product_qty

    @api.onchange('delivery_quantity')
    def _onchange_delivery_quantity(self):
        if self.product_line_id and self.product_line_id.product_qty < self.delivery_quantity:
            raise Warning("Product delivery quantity should not be greater than PO quantity.")


class POInvoicesAndPayments(models.Model):
    _name = "po.invoices.and.payments"
    _description = "PO Invoices and Payments Line"
    _rec_name = "si_no"

    si_no = fields.Char('SI No.', required=True)
    si_date = fields.Date('SI Date', default=fields.Date.today())
    si_amount = fields.Float('SI Amount')
    edts_ref_no = fields.Char('EDTS Reference No.')
    amount_released = fields.Float('Amount Released')
    or_number = fields.Char('OR No.')
    po_id = fields.Many2one('purchase.order', string='PO #')
    product_line = fields.One2many('po.invoices.and.payments.product.line', 'po_inv_payment_id', string='Product Lines')


class POInvoicesAndPaymentsLine(models.Model):
    _name = "po.invoices.and.payments.product.line"
    _description = "PO Invoices and Payments Product Line"

    name = fields.Char(string="Description")
    po_inv_payment_id = fields.Many2one('po.invoices.and.payments', string='SI No.')
    po_id = fields.Many2one('purchase.order', string='PO No.')
    product_line_id = fields.Many2one('purchase.order.line', string='Product', required=True)
    si_amount = fields.Float(string='SI Amount')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.onchange('product_line_id')
    def _onchange_type(self):
        self.name = self.product_line_id.name
        self.si_amount = self.product_line_id.price_unit

    @api.onchange('si_amount')
    def _onchange_si_amount(self):
        if self.product_line_id and self.product_line_id.price_unit < self.si_amount:
            raise Warning("SI amount should not be greater than PO product price.")
