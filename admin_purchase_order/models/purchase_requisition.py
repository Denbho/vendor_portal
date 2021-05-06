from odoo import fields, models, api
import re


class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    purchase_order_line_ids = fields.Many2many("purchase.order.line", 'pr_line_po_line_rel',
                                               compute="_get_po_line_related")

    def _get_po_line_related(self):
        po_line_obj = self.env['purchase.order.line']
        for r in self:
            r.purchase_order_line_ids = []
            if r.request_id and r.company_id and r.material_code:
                po_lines = po_line_obj.sudo().search([
                    ('company_id', '=', r.company_id.id),
                    ('product_id.default_code', '=', r.material_code),
                    ('pr_references', 'ilike', r.request_id.name)
                ])
                po_line_ids = list()
                if po_lines[:1]:
                    for rec in po_lines:
                        pr_ref = re.split('; |, |\*|\n', rec.pr_references)
                        if r.request_id.name in pr_ref:
                            po_line_ids.append(rec.id)
                r.purchase_order_line_ids = po_line_ids
