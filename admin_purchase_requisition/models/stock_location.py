# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.osv import expression


class LocationPlant(models.Model):
    _name = "location.plant"
    _description = "Plant Location"
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(LocationPlant, self).default_get(fields)
        if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
            res['barcode'] = res['complete_name']
        return res

    name = fields.Char('Location Name', required=True)
    complete_name = fields.Char("Full Location Name", compute='_compute_complete_name', store=True)
    active = fields.Boolean('Active', default=True,
                            help="By unchecking the active field, you may hide a location without deleting it.")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=True,
                                 help='Let this field empty if this location is shared between companies')
    company_code = fields.Char(string="Company Code")
    barcode = fields.Char('Barcode', copy=False)
    code = fields.Char(string="Code", copy=False)
    location_ids = fields.One2many('stock.location', 'plant_id', string="Locations")

    _sql_constraints = [('barcode_company_uniq', 'unique (barcode,company_id)',
                         'The barcode for a Plant must be unique per company!'),
                        ('code_company_uniq', 'unique (code,company_id)',
                         'The Code for a Plant must be unique per company!'),
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
        res = super(LocationPlant, self).create(vals)
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
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('barcode', operator, name), ('complete_name', operator, name),
                      ('code', operator, name)]
        plant_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(plant_ids).with_user(name_get_uid))


class Location(models.Model):
    _name = "stock.location"
    _description = "Inventory Locations"
    _parent_name = "location_id"
    _parent_store = True
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(Location, self).default_get(fields)
        if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
            res['barcode'] = res['complete_name']
        return res

    name = fields.Char('Location Name', required=True)
    plant_id = fields.Many2one('location.plant', string="Plant", ondelete='cascade')
    plant_code = fields.Char(string="Plant Code", store=True, related="plant_id.code")
    complete_name = fields.Char("Full Location Name", compute='_compute_complete_name', store=True)
    active = fields.Boolean('Active', default=True,
                            help="By unchecking the active field, you may hide a location without deleting it.")
    usage = fields.Selection([
        ('supplier', 'Vendor Location'),
        ('view', 'View'),
        ('internal', 'Internal Location'),
        ('customer', 'Customer Location'),
        ('inventory', 'Inventory Loss'),
        ('production', 'Production'),
        ('transit', 'Transit Location')], string='Location Type',
        default='internal', index=True, required=True,
        help="* Vendor Location: Virtual location representing the source location for products coming from your vendors"
             "\n* View: Virtual location used to create a hierarchical structures for your warehouse, aggregating its child locations ; can't directly contain products"
             "\n* Internal Location: Physical locations inside your own warehouses,"
             "\n* Customer Location: Virtual location representing the destination location for products sent to your customers"
             "\n* Inventory Loss: Virtual location serving as counterpart for inventory operations used to correct stock levels (Physical inventories)"
             "\n* Production: Virtual counterpart location for production operations: this location consumes the components and produces finished products"
             "\n* Transit Location: Counterpart location that should be used in inter-company or inter-warehouses operations")
    location_id = fields.Many2one(
        'stock.location', 'Parent Location', index=True, ondelete='cascade', check_company=True,
        help="The parent location that includes this location. Example : The 'Dispatch Zone' is the 'Gate 1' parent location.")
    child_ids = fields.One2many('stock.location', 'location_id', 'Contains')
    comment = fields.Text('Additional Information')
    posx = fields.Integer('Corridor (X)', default=0, help="Optional localization details, for information purpose only")
    posy = fields.Integer('Shelves (Y)', default=0, help="Optional localization details, for information purpose only")
    posz = fields.Integer('Height (Z)', default=0, help="Optional localization details, for information purpose only")
    parent_path = fields.Char(index=True)
    company_code = fields.Char(string="Company Code")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company, index=True,
        help='Let this field empty if this location is shared between companies')
    scrap_location = fields.Boolean('Is a Scrap Location?', default=False,
                                    help='Check this box to allow using this location to put scrapped/damaged goods.')
    return_location = fields.Boolean('Is a Return Location?',
                                     help='Check this box to allow using this location as a return location.')
    barcode = fields.Char('Barcode', copy=False)
    code = fields.Char(string="Code", copy=False)

    _sql_constraints = [('barcode_company_uniq', 'unique (barcode,company_id)',
                         'The barcode for a location must be unique per company !'),
                        ('code_company_uniq', 'unique (code,company_id)',
                         'The Code for a location must be unique per company !'),
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
        res = super(Location, self).create(vals)
        res.onchange_company_company_code()
        return res

    @api.depends('name', 'location_id.complete_name', 'code')
    def _compute_complete_name(self):
        for location in self:
            if location.location_id and location.usage != 'view':
                if location.code:
                    location.complete_name = '%s/%s[%s]' % (
                        location.location_id.complete_name, location.name, location.code)
                else:
                    location.complete_name = '%s/%s' % (location.location_id.complete_name, location.name)
            else:
                if location.code:
                    location.complete_name = '%s[%s]' % (location.name, location.code)
                else:
                    location.complete_name = location.name

    @api.onchange('usage')
    def _onchange_usage(self):
        if self.usage not in ('internal', 'inventory'):
            self.scrap_location = False

    def write(self, values):
        if 'company_id' in values:
            for location in self:
                if location.company_id.id != values['company_id']:
                    raise UserError(_(
                        "Changing the company of this record is forbidden at this point, you should rather archive it and create a new one."))
        return super(Location, self).write(values)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('barcode', operator, name), ('complete_name', operator, name),
                      ('code', operator, name)]
        location_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(location_ids).with_user(name_get_uid))
