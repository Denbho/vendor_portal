# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import http
import http.client
import json
import logging

_logger = logging.getLogger("_name_")


class PropertySaleRequestAccountCancel(models.TransientModel):
    _name = 'property.request.account.cancel'
    _description = "Request account to cancel"

    for_cancellation_date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    cancellation_reason_id = fields.Many2one('property.sale.cancellation.reason', string="Cancellation Reason",
                                             required=True)

    def set_account_for_cancellation(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        for r in self.env['property.admin.sale'].browse(self._context.get('active_ids')):
            conn = http.client.HTTPSConnection(api_key.api_url)
            payload = '[{\"MANDT\": \"%s\", \"VBELN\": \"%s\", \"BUKRS\": \"%s\", \"REASON\": \"%s\"}]' % (r.company_id.sap_client_id, r.so_number, r.company_id.code, self.cancellation_reason_id.id)
            conn.request("POST", "/VistaAdminAPI/rest/SOCancel/CreateSOCancel", payload, headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            r.write({
                'for_cancellation_user_id': self._uid,
                'for_cancellation': True,
                'for_cancellation_date': self.for_cancellation_date,
                'cancellation_reason_id': self.cancellation_reason_id.id,
                'cancellation_reason_code': self.cancellation_reason_id.code,
                'before_cancelled_stage_id': r.stage_id.id,
                'db_cancellation_tracker': json_data
            })
        return True
