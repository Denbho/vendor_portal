# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertyDocumentSubmissionLine(models.TransientModel):
    _name = 'property.document.submission.line'
    _description = "Validate document submitted"

    property_doc_sub_id = fields.Many2one('property.document.submission')
    document_id = fields.Many2one('property.sale.required.document', string="Document Name", required=True)
    validation_date = fields.Date(string="Validation Date", default=fields.Date.today(), required=True)
    expiry_date = fields.Date(string="Expiry Date", help="Indicate if the document has an expiry date")
    note = fields.Text(string="Notes")


class PropertyDocumentSubmission(models.TransientModel):
    _name = 'property.document.submission'
    _description = "Validate document submitted"

    line_ids = fields.One2many('property.document.submission.line', 'property_doc_sub_id')
