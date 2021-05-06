from odoo import fields, models, api, _
from datetime import datetime
import http
import http.client
import json
import logging

_logger = logging.getLogger("_name_")


class PropertySaleSubmittedDocs(models.TransientModel):
    _name = 'property.sale.submitted.docs'
    _description = "Submitted Docs"

    document_id = fields.Many2one('property.sale.required.document', string="Document Name", required=True)
    validation_date = fields.Date(string="Validation Date", default=fields.Date.today(), required=True)
    expiry_date = fields.Date(string="Expiry Date", help="Indicate if the document has an expiry date")
    note = fields.Html(string="Notes")
    submitted = fields.Boolean(string="Submitted")
    val_doc_id = fields.Many2one('property.sale.validate.submitted.docs')


class PropertySaleValidateSubmittedDocs(models.TransientModel):
    _name = 'property.sale.validate.submitted.docs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Validate Submitted Docs"

    @api.model
    def default_get(self, default_fields):
        res = super(PropertySaleValidateSubmittedDocs, self).default_get(default_fields)
        property_sale = self.env['property.admin.sale'].browse(self._context.get('active_id'))
        current_ducument = property_sale.sale_document_requirement_ids.ids
        docs = list()
        for r in property_sale.document_requirement_list_ids:
            if not r.id in current_ducument:
                docs.append([0, 0, {
                    'document_id': r.id,
                    'validation_date': fields.Date.today()
                }])
        res.update({
            'property_sale_id': property_sale.id,
            'doc_ids': docs
        })
        return res

    property_sale_id = fields.Many2one('property.admin.sale', index=True)
    doc_ids = fields.One2many('property.sale.submitted.docs', 'val_doc_id')

    def process_validated_docs(self):
        property_sale = self.env['property.admin.sale'].browse(self._context.get('active_id'))
        validated_docs = list()
        submitted_doc = property_sale.sale_document_requirement_ids.ids
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        for r in self.doc_ids:
            if r.submitted:
                validated_docs.append({
                    'document_id': r.document_id.id,
                    'validation_date': r.validation_date,
                    'expiry_date': r.expiry_date,
                    'note': r.note,
                    'property_sale_id': property_sale.id
                })
                submitted_doc.append(r.document_id.id)
                conn = http.client.HTTPSConnection(api_key.api_url)
                payload = '[{\"MANDT\": \"%s\", \"VBELN\": \"%s\", \"CODEGRUPPE\": \"%s\", \"CODE\": \"%s\", \"DATETIME\": \"%s\"}]' % (
                    property_sale.company_id.sap_client_id, property_sale.so_number, r.document_id.group_code,
                    r.document_id.code, datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
                conn.request("POST", "/VistaAdminAPI/rest/DocsOdooMaintenance/CreateDocs", payload, headers)
                res = conn.getresponse()
                data = res.read()
                json_data = json.loads(data.decode("utf-8"))
                # _logger.info(f"\n\n\nSubmitted doc: {str(json_data)}\nPayload: {payload}")
        for r in validated_docs:
            self.env['property.document.submission.line'].create(r)
        email_temp = self.env.ref('property_admin_monitoring.email_template_notif_validated_document')
        self.message_post_with_template(email_temp.id)
        property_sale.write({'sale_document_requirement_ids': [(6, 0, submitted_doc)]})
        return {'type': 'ir.actions.act_window_close'}
