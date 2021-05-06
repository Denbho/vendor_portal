from odoo import fields, models, api


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    project_subdivision_ids = fields.Many2many('property.subdivision.phase', 'helpdesk_team_subdivision_rel', string="Subdivision Project Assignments")


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    so_number = fields.Char('Property SO Number')
    property_sale_id = fields.Many2one('property.admin.sale', string="Property", store=True, compute="_get_property_sale")
    be_code = fields.Char(string="BE Code", store=True, compute="_get_property_sale")
    project_subdivision_id = fields.Many2one('property.subdivision.phase', string="Subdivision",
                                             store=True, compute="_get_property_sale")

    partner_id = fields.Many2one('res.partner', string='Customer', store=True, compute="_get_property_sale_partner",
                                 inverse="_get_inverse_property_sale_partner")
    partner_name = fields.Char(string='Customer Name', store=True, compute="_get_property_sale_partner",
                                 inverse="_get_inverse_property_sale_partner")
    partner_email = fields.Char(string='Customer Email', store=True, compute="_get_property_sale_partner",
                                 inverse="_get_inverse_property_sale_partner")

    @api.depends('so_number')
    def _get_property_sale_partner(self):
        property_sale = self.env['property.admin.sale']
        for r in self:
            property_data = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
            r.partner_id = property_data[:1] and property_data.partner_id or False
            r.partner_name = property_data[:1] and property_data.partner_id.name or None
            r.partner_name = property_data[:1] and property_data.partner_id.email or None

    def _get_inverse_property_sale_partner(self):
        for r in self:
            continue

    @api.depends('so_number')
    def _get_property_sale(self):
        property_sale = self.env['property.admin.sale']
        for r in self:
            property_data = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
            r.property_sale_id = property_data[:1] and property_data.id or False
            r.be_code = property_data[:1] and property_data.be_code or None
            r.project_subdivision_id = property_data[:1] and property_data.subdivision_phase_id or False