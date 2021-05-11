from odoo import fields, models, api

class AdminLinkVendorItemToProduct(models.TransientModel):
    _name = 'admin.link.vendor.item.to.product'
    _description = 'Link Vendor Item to Product'

    vendor_product_line_id = fields.Many2one('product.service.offered', string="Vendor Product Line")
    product_id = fields.Many2one('product.product', string="Product", required=True)
    name = fields.Char(related="vendor_product_line_id.name")
    product_service = fields.Char(related="vendor_product_line_id.product_service")
    partner_id = fields.Many2one(related="vendor_product_line_id.partner_id")
    uom_id = fields.Many2one(related="vendor_product_line_id.uom_id")
    price = fields.Float(related="vendor_product_line_id.price")
    product_category_id = fields.Many2one(related="vendor_product_line_id.product_category_id")

    def link_to_product(self):
        self.vendor_product_line_id.write({'product_id': self.product_id.id, 'button_label_type': 'open_product'})
        return {'type': 'ir.actions.act_window_close'}
