# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AdminPurchaseRequisition(models.Model):
    _inherit = 'admin.purchase.requisition'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

class PurchaseRequisitionMaterialDetails(models.Model):
    _inherit = 'purchase.requisition.material.details'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PODeliveryLine(models.Model):
    _inherit = 'po.delivery.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

class PODeliveryProductLine(models.Model):
    _inherit = 'po.delivery.product.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AdminSalesInvoice(models.Model):
    _inherit = 'admin.sales.invoice'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AdminInvoicePayment(models.Model):
    _inherit = 'admin.invoice.payment'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ContractsAndAgreements(models.Model):
    _inherit = 'contracts.and.agreements'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ContractsAndAgreementsInclusion(models.Model):
    _inherit = 'contracts.and.agreements.inclusion'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class Company(models.Model):
    _inherit = 'res.company'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AcctAssignmentCategory(models.Model):
    _inherit = 'acct.assignment.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchaseRequisitioner(models.Model):
    _inherit = 'purchase.requisitioner'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PurchasingGroup(models.Model):
    _inherit = 'purchasing.group'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class LocationPlant(models.Model):
    _inherit = 'location.plant'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class StockLocation(models.Model):
    _inherit = 'stock.location'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PRDocumentType(models.Model):
    _inherit = 'pr.document.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PODocumentType(models.Model):
    _inherit = 'admin.po.document.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class MaterialGroups(models.Model):
    _inherit = 'product.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class UnitsofMeasure(models.Model):
    _inherit = 'uom.uom'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class UnitsofMeasureCategories(models.Model):
    _inherit = 'uom.category'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")
