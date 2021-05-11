# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _

class EventEvent(models.Model):
    _inherit = "event.event"

    bid_id = fields.Many2one('purchase.bid', 'Bid No.')
