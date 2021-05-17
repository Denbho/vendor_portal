# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import locale
import math


def roundup(val, round_val):
    return math.ceil(val / round_val) * round_val


class PropertyPriceRange(models.Model):
    _name = 'property.price.range'
    _description = 'Property Price Range'

    range_from = fields.Float(string="From", required=True)
    range_to = fields.Float(string="To", required=True)
    name = fields.Char(string="Display Range", store=True, compute="_get_range_name")

    @api.depends('range_from', 'range_to')
    def _get_range_name(self):
        for i in self:
            if i.range_from and i.range_to:
                i.name = f"Php {locale.format('%0.2f', i.range_from, grouping=True)} - Php {locale.format('%0.2f', i.range_to, grouping=True)}"

    @api.constrains('range_from', 'range_to')
    def _check_range(self):
        if self.range_from >= self.range_to:
            raise ValidationError(_('"Range To" must greate than "Range From" value.'))


class PropertyModelType(models.Model):
    _name = 'property.model.type'
    _description = 'Property Descriptions'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    code = fields.Char(string="Code")


class PropertyModelUnitType(models.Model):
    _name = 'property.model.unit.type'
    _description = 'Property Unit Type'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    code = fields.Char(string="Code")


class HousingModel(models.Model):
    _name = 'housing.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Housing Models'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Model", required=True, track_visibility="always")
    # property_type = fields.Selection([
    #     ('House and Lot', 'House and Lot'),
    #     ('House & Lot', 'House & Lot'),
    #     ('House Only', 'House Only'),
    #     ('Condo', 'Condo Unit'),
    #     ('Parking Condo', 'Condo and Parking'),
    #     ('Lot Only', 'Lot Only'),
    #     ('Parking Only', 'Parking Only'),
    #     ('Others', 'Others')
    # ], string="Usage Type", default="House", required=True)

    property_type = fields.Selection([
        ('Combo Condo Unit', 'Combo Condo Unit'),
        ('Condo Parking', 'Condo Parking'),
        ('Condo', 'Condo Only'),
        ('Combo House & Lot', 'Combo House & Lot'),
        ('House & Lot', 'House & Lot'),
        ('House Only', 'House Only'),
        ('Lot Only', 'Lot Only'),
        ('Combo Lot Only', 'Combo Lot Only'),
        ('unspecified', 'Unspecified')
    ], string="Usage Type", defualt="unspecified", required=False)

    model_type_id = fields.Many2one("property.model.type", string="House Class", track_visibility="always")
    description = fields.Html(string="Description", track_visibility="always")
    year_month = fields.Char(string="Year Month", track_visibility="always")
    material_number = fields.Char(string="Material Number", track_visibility="always", required=True)
    image = fields.Binary(string="Image")
    model_blue_print = fields.Binary(string="Blue Print", attachment=True, store=True)
    house_series = fields.Char(string="House Series", track_visibility="always")
    unit_type = fields.Char(string="Unit Type", track_visibility="always")

    @api.model
    def create(self, vals):
        if vals.get('property_type') and vals.get('property_type') == 'House & Lot':
            vals['property_type'] = 'House and Lot'
        if vals.get('property_type') and not vals.get('property_type') in ['House and Lot', 'House Only', 'Condo',
                                                                           'Parking Condo', 'Lot Only', 'Parking Only',
                                                                           'Others']:
            vals['property_type'] = 'Others'
        return super(HousingModel, self).create(vals)

    # def unlink(self):
    #     for rec in self:
    #         properties = self.env['property.detail'].search([('house_model_id', '=', self.id)])
    #         if properties[:1]:
    #             msg = ""
    #             count = 1
    #             for r in properties:
    #                 msg += f"{count}. {properties.name}\n"
    #                 count += 1
    #             raise ValidationError(_(f'Delete first the properties associated to this housing model\n{msg}'))
    #         return super(HousingModel, self).unlink()


class PropertySubdivision(models.Model):
    _name = "property.subdivision"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Subdivision Profiles'
    _check_company_auto = True

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", help="Project / Subdivision", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id",
                                  check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    company_code = fields.Char(string="Company Code", related="company_id.code", store=True)
    brand = fields.Char(string="Brand")
    property_type = fields.Selection([
        ('horizontal', 'Horizontal'),
        ('vertical', 'Vertical'),
        ('both', 'Horizontal and Vertical')], string="Project Type")
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region')
    country_id = fields.Many2one('res.country', string="Country")
    island_group_id = fields.Many2one('res.island.group', string="Island Group")
    province_id = fields.Many2one('res.country.province', string="Province")
    city_id = fields.Many2one('res.country.city', string="City")
    barangay_id = fields.Many2one('res.barangay', string="Barangay")
    state_id = fields.Many2one('res.country.state', string="Region/States")
    zip = fields.Char(string="Zip Code")
    cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster I")
    cluster2_id = fields.Many2one('res.region.cluster', string="Regional Cluster II")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")

    @api.onchange('barangay_id')
    def onchange_barangay(self):
        if self.barangay_id:
            data = self.barangay_id
            self.zip = data.zip_code
            self.city_id = data.city_id and data.city_id.id

    @api.onchange('city_id')
    def onchange_city(self):
        if self.city_id:
            data = self.city_id
            self.province_id = data.province_id and data.province_id.id

    @api.onchange('province_id')
    def onchange_province(self):
        if self.province_id:
            data = self.province_id
            self.state_id = data.state_id and data.state_id.id

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            data = self.state_id
            self.island_group_id = data.island_group_id and data.island_group_id.id

    @api.onchange('island_group_id')
    def onchange_island_group(self):
        if self.island_group_id:
            data = self.island_group_id
            self.country_id = data.country_id.id

    @api.onchange('country_id')
    def onchange_country(self):
        if self.country_id:
            data = self.country_id
            self.continent_region_id = data.continent_region_id and data.continent_region_id.id

    @api.onchange('continent_region_id')
    def onchange_continent_region_i(self):
        if self.continent_region_id:
            data = self.continent_region_id
            self.continent_id = data.continent_id and data.continent_id.id


class PropertySubdivisionPhase(models.Model):
    _name = "property.subdivision.phase"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Subdivision's Projects"

    active = fields.Boolean(default=True)
    auto_send_soa = fields.Boolean(string="Auto Send SOA", help="Auto Send SOA via email once create in the system.")
    name = fields.Char(string="Project Name", track_visibility="always")
    be_code = fields.Char(string="BE Code", help="Business Entity Code", track_visibility="always")
    be_description = fields.Text(string="BE Description")
    description = fields.Text(string="Project Description")
    phase_type = fields.Selection([
        ('House', 'House and Lot'),
        ('Condo', 'Condo Unit')], string="Type", required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    logo = fields.Binary(related="company_id.logo")
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id",
                                  check_company=True)
    company_code = fields.Char(string="Company Code")
    brand = fields.Char(string="Brand")
    property_type = fields.Selection([
        ('horizontal', 'Horizontal'),
        ('vertical', 'Vertical'),
        ('both', 'Horizontal and Vertical')], string="Project Type")
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region')
    country_id = fields.Many2one('res.country', string="Country")
    island_group_id = fields.Many2one('res.island.group', string="Island Group")
    province_id = fields.Many2one('res.country.province', string="Province")
    city_id = fields.Many2one('res.country.city', string="City")
    barangay_id = fields.Many2one('res.barangay', string="Barangay")
    state_id = fields.Many2one('res.country.state', string="Region/States")
    zip = fields.Char(string="Zip Code")
    cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster I")
    cluster2_id = fields.Many2one('res.region.cluster', string="Regional Cluster II")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")

    @api.onchange('company_code')
    def onchange_company(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.model
    def create(self, vals):
        res = super(PropertySubdivisionPhase, self).create(vals)
        res.onchange_company()
        return res

    @api.onchange('barangay_id')
    def onchange_barangay(self):
        if self.barangay_id:
            data = self.barangay_id
            self.zip = data.zip_code
            self.city_id = data.city_id and data.city_id.id

    @api.onchange('city_id')
    def onchange_city(self):
        if self.city_id:
            data = self.city_id
            self.province_id = data.province_id and data.province_id.id

    @api.onchange('province_id')
    def onchange_province(self):
        if self.province_id:
            data = self.province_id
            self.state_id = data.state_id and data.state_id.id

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            data = self.state_id
            self.island_group_id = data.island_group_id and data.island_group_id.id

    @api.onchange('island_group_id')
    def onchange_island_group(self):
        if self.island_group_id:
            data = self.island_group_id
            self.country_id = data.country_id.id

    @api.onchange('country_id')
    def onchange_country(self):
        if self.country_id:
            data = self.country_id
            self.continent_region_id = data.continent_region_id and data.continent_region_id.id

    @api.onchange('continent_region_id')
    def onchange_continent_region_i(self):
        if self.continent_region_id:
            data = self.continent_region_id
            self.continent_id = data.continent_id and data.continent_id.id


class PropertyDetail(models.Model):
    _name = "property.detail"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Sales Units'

    _sql_constraints = [
        ('block_lot_be_code_key', 'unique(block_lot, be_code)',
         "Duplicate of Block-Lot is not allowed in the same Project!")
    ]

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'Company', index=True, compute="_get_company", store=True,
                                 inverse="_inverse_get_company", track_visibility="always")
    company_code = fields.Char(string="Company Code", index=True, track_visibility="always")
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    name = fields.Char(string="Display Name")
    be_code = fields.Char(string="BE Code", help="Business Entity Code")
    brand = fields.Char(string="Brand", related="subdivision_phase_id.brand", store=True)
    su_number = fields.Char(string="SU Number", required=True, track_visibility="always")
    block_lot = fields.Char(string="Block-Lot", required=True, track_visibility="always")
    property_type = fields.Selection([
        ('Combo Condo Unit', 'Combo Condo Unit'),
        ('Condo Parking', 'Condo Parking'),
        ('Condo', 'Condo Only'),
        ('Combo House & Lot', 'Combo House & Lot'),
        ('House & Lot', 'House & Lot'),
        ('House Only', 'House Only'),
        ('Lot Only', 'Lot Only'),
        ('Combo Lot Only', 'Combo Lot Only'),
        ('unspecified', 'Unspecified')
    ], string="Usage Type", defualt="unspecified", track_visibility="always")
    state = fields.Selection([
        ('Ongoing', 'Ongoing'),
        ('NRFO', 'NRFO'),
        ('RFO', 'RFO'),
        ('Lot Only', 'Lot Only'),
        ('BTS', 'BTS'),
        ('Others', 'Others')],
        string="House Unit Status", track_visibility="always", default='NRFO')
    property_status = fields.Selection([
        ('Not for Sale', 'Not for Sale'),
        ('Available for Sale', 'Available for Sale'),
        ('With Sales Quotation', 'With Sales Quotation'),
        ('Sold', 'Sold'),
        ('On Hold', 'On Hold')],
        string="Property Status", track_visibility="always", default='Not for Sale')
    subdivision_phase_id = fields.Many2one('property.subdivision.phase', string="Project", store=True,
                                           compute="_get_project_detail",
                                           inverse="_inverse_get_project_detail")
    house_model_id = fields.Many2one('housing.model', string="Unit/House Model")
    house_model_description = fields.Text(string="House Model Description", track_visibility="always")
    material_number = fields.Char(string="Material Number", track_visibility="always")
    model_type_id = fields.Many2one("property.model.type", string="House Class", track_visibility="always")
    model_unit_type_id = fields.Many2one("property.model.unit.type", string="Unit Type (Depricated)", track_visibility="always")
    house_series = fields.Char(string="House Series", store=True, related="house_model_id.unit_type")
    unit_type = fields.Char(string="Unit Type", store=True, related="house_model_id.unit_type")
    # Property Details
    category = fields.Selection([('economic', 'Economic'), ('socialized', 'Socialized')], string="Series",
                                track_visibility="always")
    miscellaneous_charge = fields.Float(string="Miscellaneous Charge", track_visibility="always")
    lot_area_price = fields.Monetary(string="Lot Area Price", track_visibility="always")
    floor_area_price = fields.Monetary(string="Floor Area Price", track_visibility="always")
    floor_area = fields.Float(string="Floor Area", track_visibility="always")
    lot_area = fields.Float(string="Lot Area", track_visibility="always")
    miscellaneous_value = fields.Monetary(string="MCC2", help="Miscellaneous Absolute Value")
    house_price = fields.Monetary(string="House Price")
    house_repair_price = fields.Monetary(string="House Repair Price", track_visibility="always")
    parking_price = fields.Monetary(string="Parking Price", track_visibility="always")
    lot_price = fields.Monetary(string="Lot Price", track_visibility="always")
    condo_price = fields.Monetary(string="Condo Price", track_visibility="always")
    premium_price = fields.Monetary(string="Premium Price", track_visibility="always")
    vat = fields.Monetary(string="VAT")
    miscellaneous_amount = fields.Monetary(string="Miscellaneous Amount")
    ntcp = fields.Monetary(string="NTCP", help="Total Net Contract Price")
    tcp = fields.Monetary(string="TCP", help="Total Contract Price")
    price_range_id = fields.Many2one('property.price.range', string="Price Range",
                                     compute="get_price_range", inverse="inverse_get_price_range")
    billed_completion_status = fields.Float(string="Billed Completion Status", track_visibility="always")
    actual_completion_status = fields.Float(string="Actual Completion Status", track_visibility="always")
    so_count = fields.Integer(compute="_compute_so_count")

    def _compute_so_count(self):
        for r in self:
            r.so_count = self.env['property.admin.sale'].sudo().search_count([('property_id', '=', r.id)])

    @api.onchange('company_code')
    def onchange_company(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.depends('be_code')
    def onchange_be_code(self):
        if self.be_code:
            project = self.env['property.subdivision.phase'].sudo().search([('be_code', '=', self.be_code)], limit=1)
            if project[:1]:
                self.subdivision_phase_id = project.id

    @api.model
    def create(self, vals):
        if vals.get('property_type') and not (vals.get('property_type')).title() in ['Combo Condo Unit',
                                                                                     'Condo Parking', 'Condo',
                                                                                     'Combo House & Lot', 'House Only',
                                                                                     'House & Lot', 'Lot Only',
                                                                                     'Combo Lot Only']:
            vals['property_type'] = 'unspecified'
        else:
            vals['property_type'] = (vals.get('property_type')).title()
        if vals.get('state') and vals.get('state') == 'NON-RFO':
            vals['state'] = 'NRFO'
        if vals.get('state') and not vals.get('state') in ['Ongoing', 'NRFO', 'RFO', 'Lot Only', 'BTS', 'Others']:
            vals['state'] = 'Others'
        res = super(PropertyDetail, self).create(vals)
        res.onchange_company()
        res.onchange_be_code()
        res.onchange_get_project_house_model()
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.depends('company_code')
    def _get_company(self):
        for r in self:
            r.company_id = False
            if r.company_code:
                company = self.env['res.company'].sudo().search([('code', '=', r.company_code)], limit=1)
                if company[:1]:
                    r.company_id = company.id

    def _inverse_get_company(self):
        for r in self:
            continue

    @api.onchange('house_model_id')
    def _onchange_house_model_id(self):
        if self.house_model_id:
            self.material_number = self.house_model_id.material_number
            if self.house_model_id.model_type_id:
                self.model_type_id = self.house_model_id.model_type_id.id
            # if self.house_model_id.property_type:
            #     self.property_type = self.house_model_id.property_type

    @api.onchange('material_number')
    def onchange_get_project_house_model(self):
        if self.material_number:
            house = self.env['housing.model'].search([('material_number', '=', self.material_number)], limit=1)
            if house[:1]:
                self.house_model_id = house.id
                if house.model_type_id:
                    self.model_type_id = house.model_type_id.id
                if house.property_type:
                    self.property_type = house.property_type

    def _inverse_get_project_model(self):
        for r in self:
            continue

    @api.onchange('subdivision_phase_id')
    def _onchange_subdivision_phase_id(self):
        if self.subdivision_phase_id:
            self.be_code = self.subdivision_phase_id.be_code

    # @api.depends('block_lot', 'su_number', 'be_code')
    # def _get_display_name(self):
    #     for i in self:
    #         if i.su_number and i.block_lot:
    #             i.name = f"{i.be_code}/{i.block_lot}"

    @api.depends('be_code')
    def _get_project_detail(self):
        for r in self:
            if r.be_code:
                project = self.env['property.subdivision.phase'].search([('be_code', '=', r.be_code)], limit=1)
                if project[:1]:
                    r.subdivision_phase_id = project.id

    def _inverse_get_project_detail(self):
        for r in self:
            continue

    def _inverse_get_contract_price(self):
        for i in self:
            continue

    def inverse_get_price_range(self):
        for i in self:
            continue

    @api.depends('tcp')
    def get_price_range(self):
        for i in self:
            i.price_range_id = False
            if i.tcp:
                price_range = self.env['property.price.range'].search(
                    [('range_from', '<=', i.tcp), ('range_to', '>=', i.tcp)], limit=1)
                i.price_range_id = price_range[:1] and price_range.id or False

    # @api.depends('floor_area', 'floor_area_price', 'lot_area', 'lot_area_price',
    #              'miscellaneous_value', 'miscellaneous_charge', 'vat', 'parking_price', 'house_price')
    # def _get_contract_price(self):
    #     for i in self:
    #         house_price = roundup(i.floor_area * i.floor_area_price, 10)
    #         lot_price = roundup(i.lot_area * i.lot_area_price, 10)
    #         ntcp = sum([house_price, lot_price, i.parking_price, i.house_repair_price])
    #         miscellaneous_amount = ntcp * (i.miscellaneous_charge / 100)
    #         i.house_price = house_price
    #         i.lot_price = lot_price
    #         i.ntcp = ntcp
    #         i.miscellaneous_amount = roundup(miscellaneous_amount + i.miscellaneous_value, 10)
    #         i.tcp = roundup(sum([ntcp, miscellaneous_amount, i.vat, ]), 10)
    #         price_range = self.env['property.price.range'].search(
    #             [('range_from', '<=', i.tcp), ('range_to', '>=', i.tcp)], limit=1)
    #         i.price_range_id = price_range[:1] and price_range.id or False
