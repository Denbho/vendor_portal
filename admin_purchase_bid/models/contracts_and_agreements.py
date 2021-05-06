# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

class ContractsAndAgreements(models.Model):
    _inherit = "contracts.and.agreements"

    bid_id = fields.Many2one('purchase.bid', 'Bid Ref.')
