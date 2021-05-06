# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_group = fields.Char(string="Vendor Group")
    broker_level = fields.Char(string="Broker Level")
    property_sale_ids = fields.One2many('property.admin.sale', 'partner_id', string="Properties")
    property_sale_count = fields.Integer(compute="_get_property_sale_count")
    sales_account_number = fields.Char(string="Sale Account Number", track_visibility="always")
    commission_rate = fields.Float(string="Commission Rate", track_visibility="always")
    company_code = fields.Char(string="Company Code", track_visibility="always")
    profession = fields.Char(string="Profession", track_visibility="always")

    sap_religion = fields.Char(string="Religion", help="From SAP DATA", track_visibility="always")
    sap_title = fields.Char(string="SAP Title")
    sap_nationality = fields.Char(string="SAP Nationality")
    sap_employment_status = fields.Char(string="SAP Employment Status")
    sap_employment_country = fields.Char(string="SAP Employment Country")
    sap_city = fields.Char(string="SAP City")
    sap_country = fields.Char(string="SAP Country")
    sap_continent = fields.Char(string="SAP Continent")
    sap_province = fields.Char(String="SAP Province")
    sap_business_entity_identification = fields.Char(string="SAP Business Entity Identification")
    sap_other_field = fields.Text(string="Other SAP Data")

    def _get_property_sale_count(self):
        for r in self:
            r.property_sale_count = r.env['property.admin.sale'].sudo().search_count([('partner_id', '=', r.id)])
