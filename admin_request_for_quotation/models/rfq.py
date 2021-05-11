# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger("_name_")

class AdminRequestForQuotationCompanyQty(models.Model):
    _name = 'admin.request.for.quotation.company.qty'
    _description = 'Admin RFQ Company Quantity'

    rfq_line_id = fields.Many2one('admin.request.for.quotation.line', string="RFQ")
    product_id = fields.Many2one('product.product', string="Product", store=True, related="rfq_line_id.product_id")
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', store=True,
                                  related="rfq_line_id.product_uom")
    qty = fields.Float(string="Quantity", required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True)


class AdminVendorRFQ(models.Model):
    _name = 'admin.vendor.rfq'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string="Vendor")
    rfq_id = fields.Many2one('admin.request.for.quotation', string="RFQ", ondelete='cascade')
    rfq_line_ids = fields.One2many('admin.request.for.quotation.line.vendor', 'vendor_rfq_id')

    @api.model
    def create(self, vals):
        res = super(AdminVendorRFQ, self).create(vals)
        partners = [res.partner_id.id]
        if res.rfq_id.user_id:
            partners.append(res.rfq_id.user_id.partner_id.id)
        res.message_subscribe(partner_ids=partners)
        return res


class AdminRequestForQuotationLineVendor(models.Model):
    _name = 'admin.request.for.quotation.line.vendor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Admin RFQ Line Per Vendor'
    _rec_name = 'partner_id'

    vendor_rfq_id = fields.Many2one('admin.vendor.rfq', string="Vendor RFQ", ondelete='cascade')
    rfq_line_id = fields.Many2one('admin.request.for.quotation.line', string="RFQ", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", store=True, related="rfq_line_id.product_id")
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', store=True,
                                  related="rfq_line_id.product_uom")
    partner_id = fields.Many2one('res.partner', string="Vendor", required=True)
    prod_qty = fields.Float(string="Quantity", store=True, related="rfq_line_id.prod_qty")
    product_description = fields.Text(string="Standard Commercial Description", store=True,
                                      related="rfq_line_id.product_description")
    price = fields.Float(string="Price")
    sub_total_price = fields.Float(string="Sub-Total", store=True, compute="_get_total")
    delivery_cost = fields.Float(string="Delivery Cost")
    delivery_lead_time = fields.Integer(string="Delivery Lead Time", help="In Days")
    gross_total = fields.Float(string="Gross Total", store=True, compute="_get_total")
    warranty = fields.Text(string="Warranty")
    terms = fields.Text(string="Payment Terms")
    validity_from = fields.Date(string="Valid From")
    validity_to = fields.Date(string="Valid To")
    minimum_order_qty = fields.Float(string="Minimum Order Quantity")
    selected = fields.Selection([('selected', 'Selected'), ('not selected', 'Not Selected')])

    @api.depends('delivery_cost', 'price', 'prod_qty')
    def _get_total(self):
        for r in self:
            sub_total = r.prod_qty * r.price
            r.sub_total_price = sub_total
            r.gross_total = sub_total + r.delivery_cost


class AdminRequestForQuotationLine(models.Model):
    _name = 'admin.request.for.quotation.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Admin RFQ Line'
    _rec_name = 'rfq_id'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    rfq_id = fields.Many2one('admin.request.for.quotation', string="RFQ", ondelete='cascade')
    default_product_code = fields.Char(string="Material Code", store=True, related="product_id.default_code")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_description = fields.Text(string="Standard Commercial Description", required=True)
    product_uom_category_id = fields.Many2one('uom.category', string='Product UoM Category', store=True,
                                              compute="_get_uom_category")
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', required=True,
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_image = fields.Binary('Product Image', related="product_id.image_1920", store=False)
    latest_price = fields.Html(string='Latest Price', store=True, compute="_get_latest_price")
    prod_qty = fields.Float(string="Quantity", required=True, default=1.0, readonly=True,
                            states={'draft': [('readonly', False)], 'pending': [('readonly', False)]})
    stock_location_id = fields.Many2one('stock.location', string="Delivery Location")
    quantity_company_ids = fields.One2many('admin.request.for.quotation.company.qty', 'rfq_line_id')
    company_name = fields.Char(string="Companies", store=True, compute="_get_company_qty")

    price = fields.Float(string="Price")
    sub_total_price = fields.Float(string="Sub-Total", store=True, compute="_get_total")
    delivery_cost = fields.Float(string="Delivery Cost")
    delivery_lead_time = fields.Integer(string="Delivery Lead Time", help="In Days")
    gross_total = fields.Float(string="Gross Total", store=True, compute="_get_total")
    warranty = fields.Text(string="Warranty")
    terms = fields.Text(string="Payment Terms")
    validity_from = fields.Date(string="Valid From")
    validity_to = fields.Date(string="Valid To")
    minimum_order_qty = fields.Float(string="Minimum Order Quantity")
    vendor_ids = fields.Many2many(
        'res.partner', 'purchase_vendor_rfq_rel', string="Vendors",
        copy=False, readonly=True, states={'draft': [('readonly', False)]},
        help="Admin/Managers can add the vendors and invite for this RFQ")
    assigned_vendor_ids = fields.Many2many('res.partner', 'purchase_assigned_vendor_rfq_rel', string="Assigned Vendors",
        copy=False, help="Selected vendors for creating PO")
    vendor_rfq_line_ids = fields.One2many('admin.request.for.quotation.line.vendor', 'rfq_line_id')

    @api.depends('product_id')
    def _get_latest_price(self):
        price = self.env['product.supplierinfo']
        for i in self:
            line_values = ""
            if i.product_id:
                price_rec = price.sudo().search([('product_tmpl_id', '=', i.product_id.id)], order='id desc')
                if price_rec[:1]:
                    line_cnt = 1
                    br = "<br/>"
                    for line in price_rec:
                        if line_cnt == 3:
                            break
                        elif not line.date_end or (line.date_end and line.date_end >= date.today()):
                            line_values = line_values + "<b>Vendor: </b>" + line.name.name
                            if line.product_name:
                                line_values = line_values + br + "<b>Vendor Product Name: </b>" + line.product_name
                            if line.product_code:
                                line_values = line_values + br + "<b>Vendor Product Code: </b>" + line.product_code
                            if line.delay >= 1:
                                line_values = line_values + br + "<b>Delivery Lead Time: </b>" + str(
                                    line.delay) + " day(s)"
                            if line.min_qty != 0:
                                line_values = line_values + br + "<b>Minimum Order Qty: </b>" + str(
                                    line.min_qty) + " " + line.product_uom.name
                            line_values = line_values + br + "<b>Price: </b>" + str(line.price)
                            if line.date_start:
                                line_values = line_values + br + "<b>Validity: </b>" + str(
                                    line.date_start) + " to " + str(line.date_end)
                            line_values = line_values + br + br
                            line_cnt += 1
            i.latest_price = line_values

    @api.constrains('product_uom', 'product_id')
    def _check_uom_category(self):
        for rec in self:
            if rec.product_uom.category_id.id != rec.product_id.uom_id.category_id.id:
                raise ValidationError(_(
                    f"The Unit of Measure ({rec.product_uom.name}) used for {rec.product_id.name} does not belongs to {rec.product_id.uom_id.category_id.name} unit of measure category"))

    @api.depends('product_id', 'product_id.uom_id', 'product_id.uom_id.category_id')
    def _get_uom_category(self):
        for r in self:
            if r.product_id:
                r.product_uom_category_id = r.product_id.uom_id and r.product_id.uom_id.category_id.id or False

    @api.onchange('product_id')
    def _onchange_product(self):
        for r in self:
            if r.product_id:
                r.product_description = r.product_id.description_purchase
                r.product_uom = r.product_id.uom_po_id and r.product_id.uom_po_id.id or r.product_id.uom_id and r.product_id.uom_id.id or False

    @api.depends('delivery_cost', 'price', 'prod_qty')
    def _get_total(self):
        for r in self:
            sub_total = r.prod_qty * r.price
            r.sub_total_price = sub_total
            r.gross_total = sub_total + r.delivery_cost

    @api.depends('quantity_company_ids', 'quantity_company_ids.company_id', 'quantity_company_ids.company_id.name')
    def _get_company_qty(self):
        for r in self:
            company = ''
            for c in r.quantity_company_ids:
                if company != "":
                    company += f", {c.company_id.name}"
                else:
                    company += f"{c.company_id.name}"
            r.company_name = company


class AdminRequestForQuotation(models.Model):
    _name = 'admin.request.for.quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Admin RFQ'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sent', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    name = fields.Char('Request Reference', copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', 'Company', required=True,
                        default=lambda self: self.env.company, tracking=True,)
    user_id = fields.Many2one('res.users', string='Purchasing Officer', index=True, tracking=True,
                              default=lambda self: self.env.user)
    create_date = fields.Datetime(
        string="Created Date", readonly=True, copy=False, default=fields.Datetime.now)
    est_del_date = fields.Date(string="Required Delivery Date", copy=False, readonly=True,
                               states={'draft': [('readonly', False)], 'pending': [('readonly', False)]},
                               help="Admin/Managers can set their estimated delivery date for this rfq, "
                                    "this information will be sent to the vendors.")
    close_date = fields.Date(string="RFQ Closing Date", copy=False, readonly=True,
                             states={'draft': [('readonly', False)], 'pending': [('readonly', False)]},
                             help="Last date of quotation for the vendor")
    rfq_line_ids = fields.One2many('admin.request.for.quotation.line', 'rfq_id')
    vendor_quotation_count = fields.Integer(compute="_get_vendor_quotation_count")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('vendor.request.for.quotation')
        return super(AdminRequestForQuotation, self).create(vals)

    def set_rfq_done(self):
        vendor_rfq = self.env['admin.vendor.rfq']
        not_done_rfq = self.env['admin.request.for.quotation.line'].sudo().search([('rfq_id', '=', self.id), ('state', '!=', 'cancel'), ('assigned_vendor_ids', '=', False)])
        if not_done_rfq[:1]:
            items = ""
            count = 1
            for item in not_done_rfq:
                items += f"\n\t{count}. {item.product_id.name}"
                count += 1
            raise ValidationError(_(f"Please select vendor for the following item/s: {items}"))
        for l in self.env['admin.request.for.quotation.line'].sudo().search([('rfq_id', '=', self.id), ('state', '=', 'sent')]):
            l.write({'state': 'done'})
        for r in vendor_rfq.search([('rfq_id', '=', self.id)]):
            selected = False
            for i in r.rfq_line_ids:
                if i.selected == 'selected':
                    selected = True
                else:
                    i.write({'selected': 'not selected'})
            if selected:
                email_temp = self.env.ref('admin_request_for_quotation.email_template_request_for_quotation_selected_vendor')
                r.message_post_with_template(email_temp.id)
        self.write({'state': 'done'})

    def _get_vendor_quotation_count(self):
        vendor_rfq = self.env['admin.vendor.rfq']
        for r in self:
            r.vendor_quotation_count = vendor_rfq.sudo().search_count([('rfq_id', '=', r.id)])

    def create_vendor_rfq_line(self):
        vendors = list()
        rfq_material = list()
        for i in self.rfq_line_ids:
            vendors += i.vendor_ids.ids
            rfq_material.append({
                'product_id': i.product_id.id,
                'vendor_ids': i.vendor_ids.ids,
                'rfq_line_id': i.id,
            })
        # vendor_rfq = list()
        for ven in set(vendors):
            rfq = list()
            for r in rfq_material:
                if ven in r.get('vendor_ids'):
                    rfq.append([0, 0, {
                        'partner_id': ven,
                        'product_id': r.get('product_id'),
                        'rfq_line_id': r.get('rfq_line_id')
                    }
                                ])
            # vendor_rfq.append(x)
            data = self.env['admin.vendor.rfq'].create({
                    'partner_id': ven,
                    'rfq_id': self.id,
                    'rfq_line_ids': rfq
                })
            email_temp = self.env.ref('admin_request_for_quotation.email_template_request_for_quotation')
            data.message_post_with_template(email_temp.id)
            for r in self.rfq_line_ids:
                r.write({'state': 'sent'})
        self.write({'state': 'sent'})
        return True
