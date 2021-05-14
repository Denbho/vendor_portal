# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.osv import expression


class PRDocumentType(models.Model):
    _name = 'pr.document.type'
    _description = 'PR Document Type'
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(PRDocumentType, self).default_get(fields)
        if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
            res['barcode'] = res['complete_name']
        return res

    name = fields.Char('PR Document Type Name', required=True)
    complete_name = fields.Char("Full PR Doc Type Name", compute='_compute_complete_name', store=True)
    active = fields.Boolean('Active', default=True,
                            help="By unchecking the active field, you may hide a pr doc type without deleting it.")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=True,
                                 help='Let this field empty if this pr doc type is shared between companies')
    company_code = fields.Char(string="Company Code")
    barcode = fields.Char('Barcode', copy=False)
    code = fields.Char(string="Code", copy=False)

    _sql_constraints = [('barcode_company_uniq', 'unique (barcode,company_id)',
                         'The barcode for a Plant must be unique per company!'),
                        ('code_company_uniq', 'unique (code,company_id)',
                         'The Code for a PR Doc Type must be unique per company!'),
                        ]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.model
    def create(self, vals):
        res = super(PRDocumentType, self).create(vals)
        res.onchange_company_company_code()
        return res

    @api.depends('name', 'code')
    def _compute_complete_name(self):
        for plant in self:
            if plant.code:
                plant.complete_name = '%s[%s]' % (plant.name, plant.code)
            else:
                plant.complete_name = plant.name

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        args = args or []
        domain = []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('barcode', operator, name), ('complete_name', operator, name),
                      ('code', operator, name)]
        pr_doc_type_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(pr_doc_type_ids).with_user(name_get_uid))
