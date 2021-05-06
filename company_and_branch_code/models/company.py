# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    code = fields.Char(string="Code")


# class ResBranch(models.Model):
#     _inherit = 'res.branch'
#
#     code = fields.Char(string="Code")


