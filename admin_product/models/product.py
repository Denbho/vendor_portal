# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(string='Material Code / SKU')
    categ_id = fields.Many2one('product.category', string='Material Group')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char('Material Code / SKU')


class ProductCategory(models.Model):
    _inherit = "product.category"
    _description = "Material Group"

    parent_id = fields.Many2one('product.category', 'Parent Group', index=True, ondelete='cascade')
    child_id = fields.One2many('product.category', 'parent_id', 'Child Group')
