# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning

class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    bid_id = fields.Many2one('purchase.bid', string='Bid No.', copy=False)
