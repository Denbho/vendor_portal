# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [('partner_assign_number', 'CHECK(partner_assign_number IS NOT NULL AND unique(partner_assign_number))',
                         'The "Unique Customer Number" field  must have unique value!')]

    partner_assign_number = fields.Char(string="Customer Number", help="Unique Customer Number")
