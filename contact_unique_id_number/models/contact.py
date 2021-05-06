# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [('partner_assign_number', 'unique(partner_assign_number)',
                         'The "Unique Customer Number" field  must have unique value!')]

    partner_assign_number = fields.Char(string="CN #", help="Unique Customer Number")
