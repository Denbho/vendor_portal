# -*- coding: utf-8 -*-

from odoo import fields, models, api


_CONTENT_TYPE = [
    ('application/json', 'application/json')
]


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_app_key = fields.Char(string="API AppKey")
    api_app_id = fields.Char(string="API AppID")
    api_content_type = fields.Selection(_CONTENT_TYPE, string="API Content Type")
    api_url = fields.Char(string="API URL")

    @api.model
    def default_get(self, fields):
        settings = super(ResConfigSettings, self).default_get(fields)
        settings.update(self.get_admin_api_key_config_data(fields))
        return settings

    @api.model
    def get_admin_api_key_config_data(self, fields):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        return {
            'api_app_key': api_key.api_app_key,
            'api_app_id': api_key.api_app_id,
            'api_content_type': api_key.api_content_type,
            'api_url': api_key.api_url
        }

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        vals = {
            'api_app_key': self.api_app_key,
            'api_app_id': self.api_app_id,
            'api_content_type': self.api_content_type,
            'api_url': self.api_url
        }
        api_key.write(vals)


class AdminApiKeyConfig(models.Model):
    _name = 'admin.api.key.config'
    _description = "API Key Configuration"

    api_app_key = fields.Char(string="API AppKey")
    api_app_id = fields.Char(string="API AppID")
    api_content_type = fields.Selection(_CONTENT_TYPE, string="API Content Type", default='application/json')
    api_url = fields.Char(string="API URL")