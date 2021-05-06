# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_hbd_email_template_id(self):
        return self.env.ref('ips_partner_dob.email_template_partner_happy_birthday', False)

    date_of_birth = fields.Date(string='Date of Birth', index=True)
    dyob = fields.Integer("Day of Birth", compute='_compute_yy_mm_of_birth', store=True, index=True,
                         help="The day of birth from the Date of Birth.")
    mob = fields.Integer(string='Month of Birth', compute='_compute_yy_mm_of_birth', store=True, index=True,
                         help="The month of birht from the Date of Birth.")
    yob = fields.Integer(string='Year of Birth', compute='_compute_yy_mm_of_birth', store=True, index=True,
                         help="The year of birth from the Date of Birth.")
    send_hbd_email = fields.Boolean(string='Send Birthday Email')
    hbd_email_template_id = fields.Many2one('mail.template', string='Birthday Email Template', default=_get_default_hbd_email_template_id)
    last_hbd_email_sent = fields.Date(string='Last Birthday Email Sent', help="Last Birthday Email was sent to this partner on this date")

    @api.depends('date_of_birth')
    def _compute_yy_mm_of_birth(self):
        for r in self:
            if not r.date_of_birth:
                r.mob = False
                r.yob = False
                r.dyob = False
            else:
                year, month, day = self.split_date(fields.Date.from_string(r.date_of_birth))
                r.dyob = day
                r.mob = month
                r.yob = year

    @api.onchange('send_hbd_email')
    def _onchange_send_hbd_email(self):
        if self.send_hbd_email and not self.hbd_email_template_id:
            self.hbd_email_template_id = self._get_default_hbd_email_template_id()


    def action_send_happy_birthday_email(self):
        for r in self:
            if not r.hbd_email_template_id:
                raise ValidationError(_("Could not send Happy Birthday Email message to the partner '%s'"
                                        " when there was no Email Template specified for the partner.")
                                        % (r.display_name,))
            r.message_post_with_template(r.hbd_email_template_id.id)
        self.write({
            'last_hbd_email_sent': fields.Date.today(),
            })


    def cron_send_happy_birthday_email(self):
        today_str = fields.Date.today()
        current_year, current_month, current_day = self.split_date(fields.Date.from_string(today_str))

        partner_to_send = self.search([
            ('email', '!=', False),
            ('send_hbd_email', '=', True),
            ('mob', '=', current_month),
            ('dyob', '=', current_day),
            ('hbd_email_template_id', '!=', False),
            '|', ('last_hbd_email_sent', '=', False), ('last_hbd_email_sent', '!=', today_str)
            ])
        partner_to_send.action_send_happy_birthday_email()

    def split_date(self, date):
        """
        Method to split a date into year,month,day separatedly
        @param date date:
        """
        year = date.year
        month = date.month
        day = date.day
        return year, month, day