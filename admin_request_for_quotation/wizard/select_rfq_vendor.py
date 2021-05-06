from odoo import fields, models, api
from odoo.exceptions import ValidationError


class AdminSelectVendorRFQ(models.TransientModel):
    _name = 'admin.select.vendor.rfq'
    _description = 'Select Vendor for RFQ Item'

    rfq_line_id = fields.Many2one('admin.request.for.quotation.line', string="RFQ")
    rfq_vendor_id = fields.Many2one('admin.request.for.quotation.line.vendor', string="Vendor RFQ",
                                    domain="[('rfq_line_id', '=',rfq_line_id), ('selected', '!=', 'selected')]",required=True)
    product_id = fields.Many2one('product.product', string="Product", related="rfq_vendor_id.product_id")
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', related="rfq_vendor_id.product_uom")
    prod_qty = fields.Float(string="Quantity", related="rfq_vendor_id.prod_qty")
    price = fields.Float(string="Price", related="rfq_vendor_id.price")
    sub_total_price = fields.Float(string="Sub-Total", related="rfq_vendor_id.sub_total_price")
    delivery_cost = fields.Float(string="Delivery Cost", related="rfq_vendor_id.delivery_cost")
    delivery_lead_time = fields.Integer(string="Delivery Lead Time", help="In Days", related="rfq_vendor_id.delivery_lead_time")
    gross_total = fields.Float(string="Gross Total", related="rfq_vendor_id.gross_total")
    warranty = fields.Text(string="Warranty", related="rfq_vendor_id.warranty")
    terms = fields.Text(string="Payment Terms", related="rfq_vendor_id.terms")
    validity_from = fields.Date(string="Valid From", related="rfq_vendor_id.validity_from")
    validity_to = fields.Date(string="Valid To", related="rfq_vendor_id.validity_to")
    minimum_order_qty = fields.Float(string="Minimum Order Quantity", related="rfq_vendor_id.minimum_order_qty")
    product_description = fields.Text(string="Standard Commercial Description", store=True,
                                      related="rfq_vendor_id.product_description")

    def select_vendor(self):
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")
        for r in self.rfq_vendor_id.rfq_line_id.vendor_rfq_line_ids:
            if r.id == self.rfq_vendor_id.id:
                r.write({'selected': 'selected'})
        assigned_vendor_ids = [line.id for line in self.rfq_vendor_id.rfq_line_id.assigned_vendor_ids]
        assigned_vendor_ids.append(self.rfq_vendor_id.partner_id.id)
        self.rfq_vendor_id.rfq_line_id.write({
            'assigned_vendor_ids': [(6, 0, assigned_vendor_ids)],
            'price': self.price,
            'delivery_cost': self.delivery_cost,
            'delivery_lead_time': self.delivery_lead_time,
            'warranty': self.warranty,
            'terms': self.terms,
            'validity_from': self.validity_from,
            'validity_to': self.validity_to,
            'minimum_order_qty': self.minimum_order_qty
        })
        vendor_pricelist = []
        create_update_pricelist = True
        if self.validity_from and self.validity_to:
            vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', self.product_id.id), ('name', '=', self.rfq_vendor_id.partner_id.id), ('date_start', '>=', self.validity_from), ('date_end', '<=', self.validity_to), ('price', '=', self.price)])
            between_validity_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', self.product_id.id), ('name', '=', self.rfq_vendor_id.partner_id.id), ('date_start', '<=', self.validity_from), ('date_end', '>=', self.validity_to), ('price', '=', self.price)])
            if between_validity_pricelist:
                create_update_pricelist = False
        else:
            vendor_pricelist = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', self.product_id.id), ('name', '=', self.rfq_vendor_id.partner_id.id), ('date_start', '=', False), ('date_end', '=', False)])
        if create_update_pricelist:
            if vendor_pricelist:
                for line in vendor_pricelist:
                    line.write({
                        'date_start': self.validity_from,
                        'date_end': self.validity_to,
                        'min_qty': self.minimum_order_qty,
                        'product_uom': self.product_uom.id,
                        'price': self.price,
                        'delay': self.delivery_lead_time,
                    })
            else:
                self.env['product.supplierinfo'].sudo().create({
                    'product_tmpl_id': self.product_id.id,
                    'name': self.rfq_vendor_id.partner_id.id,
                    'date_start': self.validity_from,
                    'date_end': self.validity_to,
                    'min_qty': self.minimum_order_qty,
                    'product_uom': self.product_uom.id,
                    'price': self.price,
                    'delay': self.delivery_lead_time,
                })
        return {'type': 'ir.actions.act_window_close'}
