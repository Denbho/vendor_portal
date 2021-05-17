# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class Company(models.Model):
    _inherit = 'res.company'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class Contact(models.Model):
    _inherit = 'res.partner'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyFinancingTypeTerm(models.Model):
    _inherit = 'property.financing.type.term'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyFinancingType(models.Model):
    _inherit = "property.financing.type"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyDownpaymentTerm(models.Model):
    _inherit = "property.downpayment.term"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleRequiredDocument(models.Model):
    _inherit = 'property.sale.required.document'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleCancellationReason(models.Model):
    _inherit = 'property.sale.cancellation.reason'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyStatusAssignedPerson(models.Model):
    _inherit = 'property.status.assigned.person'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleDocumentStatusBrand(models.Model):
    _inherit = 'property.sale.document.status.project'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatus(models.Model):
    _inherit = 'property.sale.status'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatus(models.Model):
    _inherit = 'property.sale.sub.status'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleBankLoanApplication(models.Model):
    _inherit = 'property.sale.bank.loan.application'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyAdminSale(models.Model):
    _inherit = 'property.admin.sale'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleSOAOverdueLine(models.Model):
    _inherit = 'property.sale.soa.overdue.line'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySaleStatementOfAccount(models.Model):
    _inherit = 'property.sale.statement.of.account'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyLedgerPaymentItem(models.Model):
    _inherit = 'property.ledger.payment.item'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")

    _sql_constraints = [
        ('so_number_client_line_counter', 'unique(so_number, sap_client_id, line_counter)',
         "Duplicate of payments is not allowed in the so number, client_id and line_counter!")
    ]


class PropertyPriceRange(models.Model):
    _inherit = 'property.price.range'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyModelType(models.Model):
    _inherit = 'property.model.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyModelUnitType(models.Model):
    _inherit = 'property.model.unit.type'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class HousingModel(models.Model):
    _inherit = 'housing.model'

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySubdivision(models.Model):
    _inherit = "property.subdivision"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertySubdivisionPhase(models.Model):
    _inherit = "property.subdivision.phase"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")


class PropertyDetail(models.Model):
    _inherit = "property.detail"

    sap_client_id = fields.Integer(string="Client ID")
    sap_datetime_sync = fields.Datetime(string="SAP Datetime Sync")
