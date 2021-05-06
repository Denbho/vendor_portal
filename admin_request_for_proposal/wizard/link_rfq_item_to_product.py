from odoo import fields, models, api

class AdminLinkRFPItemToProduct(models.TransientModel):
    _name = 'admin.link.rfp.item.to.product'
    _description = 'Link RFP Item to Product'

    rfp_product_line_id = fields.Many2one('admin.request.for.proposal.line.product', string="RFP Product Line")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_name = fields.Char(related="rfp_product_line_id.product_name")
    name = fields.Text(related="rfp_product_line_id.name")
    qty = fields.Float(related="rfp_product_line_id.qty")
    unit_name = fields.Char(related="rfp_product_line_id.unit_name")
    price = fields.Float(related="rfp_product_line_id.price")
    total = fields.Float(related="rfp_product_line_id.total")
    delivery_lead_time = fields.Float(related="rfp_product_line_id.delivery_lead_time")
    validity_from = fields.Date(related="rfp_product_line_id.validity_from")
    validity_to = fields.Date(related="rfp_product_line_id.validity_to")

    def link_to_product(self):
        self.rfp_product_line_id.write({'product_id': self.product_id.id})
        return {'type': 'ir.actions.act_window_close'}
