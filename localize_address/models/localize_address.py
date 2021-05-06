# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.osv import expression
import logging

_logger = logging.getLogger("_name_")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region')
    country_id = fields.Many2one('res.country', string="Country")
    island_group_id = fields.Many2one('res.island.group', string="Island Group")
    province_id = fields.Many2one('res.country.province', string="Province")
    city_id = fields.Many2one('res.country.city', string="City Name")
    barangay_id = fields.Many2one('res.barangay', string="Barangay")

    @api.model
    def create(self, vals):
        barangay = list()
        if vals.get('barangay_id'):
            barangay = self.env['res.barangay'].browse(vals.get('barangay_id'))
        elif vals.get('zip'):
            barangay = self.env['res.barangay'].search([('zip_code', '=', vals.get('zip'))], limit=2)
        if barangay and barangay[:1]:
            data = barangay[:1]
            vals['zip'] = data.zip_code
            vals['barangay_id'] = len(barangay) == 1 and data.id or False
            vals['city'] = data.city_id.name
            vals['city_id'] = data.city_id.id
            vals['province_id'] = data.province_id.id
            vals['state_id'] = data.state_id.id
            vals['island_group_id'] = data.island_group_id.id
            vals['country_id'] = data.country_id.id
            vals['continent_region_id'] = data.continent_region_id.id
            vals['continent_id'] = data.continent_id.id
        # _logger.info(f"\n\n{vals}\n")
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        barangay = list()
        if vals.get('barangay_id'):
            barangay = self.env['res.barangay'].browse(vals.get('barangay_id'))
        elif vals.get('zip'):
            barangay = self.env['res.barangay'].search([('zip_code', '=', vals.get('zip'))], limit=2)
        if barangay and barangay[:1]:
            data = barangay[:1]
            vals['zip'] = data.zip_code
            vals['barangay_id'] = len(barangay) == 1 and data.id or False
            vals['city'] = data.city_id.name
            vals['city_id'] = data.city_id.id
            vals['province_id'] = data.province_id.id
            vals['state_id'] = data.state_id.id
            vals['island_group_id'] = data.island_group_id.id
            vals['country_id'] = data.country_id.id
            vals['continent_region_id'] = data.continent_region_id.id
            vals['continent_id'] = data.continent_id.id
        return super(ResPartner, self).write(vals)

    @api.onchange('barangay_id')
    def onchange_barangay(self):
        if self.barangay_id:
            data = self.barangay_id
            self.zip = data.zip_code or False
            self.city = data.name
            self.city_id = data.city_id and data.city_id.id or False

    @api.onchange('city_id')
    def onchange_city(self):
        if self.city_id:
            data = self.city_id
            self.city = data.name
            self.province_id = data.province_id and data.province_id.id or False

    @api.onchange('province_id')
    def onchange_province(self):
        if self.province_id:
            data = self.province_id
            self.state_id = data.state_id and data.state_id.id

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            data = self.state_id
            self.island_group_id = data.island_group_id and data.island_group_id.id or False
            self.country_id = data.country_id.id

    @api.onchange('island_group_id')
    def onchange_island_group(self):
        if self.island_group_id:
            data = self.island_group_id
            self.country_id = data.country_id.id or False

    @api.onchange('country_id')
    def onchange_country(self):
        if self.country_id:
            data = self.country_id
            self.continent_region_id = data.continent_region_id and data.continent_region_id.id or False

    @api.onchange('continent_region_id')
    def onchange_continent_region_i(self):
        if self.continent_region_id:
            data = self.continent_region_id
            self.continent_id = data.continent_id and data.continent_id.id or False



class ResContinent(models.Model):
    _name = 'res.continent'

    name = fields.Char(name="Continent", required=True)
    continent_region_ids = fields.One2many('res.continent.region', 'continent_id', string="Regions")


class ResContinentRegion(models.Model):
    _name = 'res.continent.region'

    name = fields.Char(string="Continent Region", required=True)
    continent_id = fields.Many2one('res.continent', string="Continent")
    country_ids = fields.One2many('res.country', 'continent_region_id', string="Countries")


class ResCountry(models.Model):
    _inherit = 'res.country'

    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    island_ids = fields.One2many('res.island.group', 'country_id', string="Islands")


class ResIslandGroup(models.Model):
    _name = 'res.island.group'

    name = fields.Char(string="Name", required=True)
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    state_ids = fields.One2many('res.country.state', 'island_group_id', string="Regional Cluster")


class ResRegionCluster(models.Model):
    _name = 'res.region.cluster'

    name = fields.Char(string="Name", required=True)
    # continent_id = fields.Many2one('res.continent', string="Continent")
    # continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    # country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    # island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    # cluster_ids = fields.One2many('res.region.cluster2', 'cluster_id', string="Regional Cluster II")


class ResRegionCluster2(models.Model):
    _name = 'res.region.cluster2'

    name = fields.Char(string="Name", required=True)
    # continent_id = fields.Many2one('res.continent', string="Continent")
    # continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    # country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    # island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    # cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster", domain="[('island_group_id', '=', island_group_id)]")
    # states_ids = fields.One2many('res.country.state', 'cluster2_id', string="States/Regions")


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster")
    cluster2_id = fields.Many2one('res.region.cluster2', string="Regional Cluster II")
    province_ids = fields.One2many('res.country.province', 'state_id', string="Provinces")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result


class ResCountryProvince(models.Model):
    _name = 'res.country.province'

    name = fields.Char(string="Name", required=True)
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    # cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster", domain="[('island_group_id', '=', island_group_id)]")
    # cluster2_id = fields.Many2one('res.region.cluster2', string="Regional Cluster II", domain="[('cluster_id', '=', cluster_id)]")
    state_id = fields.Many2one('res.country.state', string="State/Region", domain="[('country_id', '=', country_id)]")
    city_ids = fields.One2many('res.country.city', 'province_id', string="Cities")

class ResCountryCity(models.Model):
    _name = 'res.country.city'

    name = fields.Char(string="Name", required=True)
    province_capital = fields.Boolean(string="Province Capital")
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    # cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster", domain="[('island_group_id', '=', island_group_id)]")
    # cluster2_id = fields.Many2one('res.region.cluster2', string="Regional Cluster II", domain="[('cluster_id', '=', cluster_id)]")
    state_id = fields.Many2one('res.country.state', string="State/Region", domain="[('country_id', '=', country_id)]")
    province_id = fields.Many2one('res.country.province', string="Province", domain="[('state_id', '=', state_id)]")
    barangay_ids = fields.One2many('res.barangay', 'city_id', string="Barangay")


class ResBarangay(models.Model):
    _name = 'res.barangay'

    name = fields.Char(string="Name", required=True)
    zip_code = fields.Char(string="Zip Code")
    continent_id = fields.Many2one('res.continent', string="Continent")
    continent_region_id = fields.Many2one('res.continent.region', string="Continent Region", domain="[('continent_id', '=', continent_id)]")
    country_id = fields.Many2one('res.country', string="Country", domain="[('continent_region_id', '=', continent_region_id)]")
    island_group_id = fields.Many2one('res.island.group', string="Island Group", domain="[('country_id', '=', country_id)]")
    # cluster_id = fields.Many2one('res.region.cluster', string="Regional Cluster", domain="[('island_group_id', '=', island_group_id)]")
    # cluster2_id = fields.Many2one('res.region.cluster2', string="Regional Cluster II", domain="[('cluster_id', '=', cluster_id)]")
    state_id = fields.Many2one('res.country.state', string="State/Region", domain="[('country_id', '=', country_id)]")
    province_id = fields.Many2one('res.country.province', string="Province", domain="[('state_id', '=', state_id)]")
    city_id = fields.Many2one('res.country.city', string="City", domain="[('province_id', '=', province_id)]")

    def name_get(self):
        res = super(ResBarangay, self).name_get()
        data = []
        for i in self:
            display_value = f"{i.name} [{i.zip_code}] - {i.city_id.name}"
            data.append((i.id, display_value))
        return data

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', '|', ('zip_code', operator, name), ('name', operator, name), ('city_id', operator, name)]
        return super(ResBarangay, self).search(expression.AND([args, domain]), limit=limit).name_get()
