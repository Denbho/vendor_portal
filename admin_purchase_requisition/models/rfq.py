# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

class AdminRequestForQuotationCompanyQty(models.Model):
    _inherit = 'admin.request.for.quotation.company.qty'

    pr_id = fields.Many2one('admin.purchase.requisition', 'PR No.')
