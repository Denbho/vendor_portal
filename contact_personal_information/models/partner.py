# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
import locale
import logging

_logger = logging.getLogger("_name_")


class ResPartnerMonthlyIncomeRange(models.Model):
    _name = 'res.partner.monthly.income.range'
    _description = 'Monthly Income Range'

    range_from = fields.Float(string="From", required=True)
    range_to = fields.Float(string="To", required=True)
    name = fields.Char(string="Display Range", store=True, compute="_get_range_name")

    @api.depends('range_from', 'range_to')
    def _get_range_name(self):
        for i in self:
            if i.range_from and i.range_to:
                i.name = f"Php {locale.format('%0.2f', i.range_from, grouping=True)} - Php {locale.format('%0.2f', i.range_to, grouping=True)}"

    @api.constrains('range_from', 'range_to')
    def _check_range(self):
        if self.range_from >= self.range_to:
            raise ValidationError(_('"Range To" must greate than "Range From" value.'))


class ResPartnerReligion(models.Model):
    _name = "res.partner.religion"
    _description = 'Religion Sectors'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")


class ResPartnerEmploymentStatus(models.Model):
    _name = 'res.partner.employment.status'
    _description = 'Employment Status'

    name = fields.Char(string="Name", required=True)
    parent_id = fields.Many2one('res.partner.employment.status', string="Parent")
    description = fields.Text(string="Description")


class ResPartnerProfession(models.Model):
    _name = 'res.partner.profession'
    _description = 'Professional Occupation'

    name = fields.Char(string="Profession")
    description = fields.Text(string="Description")


class ResPartnerAgeRange(models.Model):
    _name = 'res.partner.age.range'
    _description = 'Age Range'

    range_from = fields.Float(string="From", required=True)
    range_to = fields.Float(string="To", required=True)
    name = fields.Char(string="Display Range", store=True, compute="_get_range_name")

    @api.depends('range_from', 'range_to')
    def _get_range_name(self):
        for i in self:
            if i.range_from and i.range_to:
                i.name = f"{int(i.range_from)} - {int(i.range_to)}"

    @api.constrains('range_from', 'range_to')
    def _check_range(self):
        if self.range_from >= self.range_to:
            raise ValidationError(_('"Range To" must greate than "Range From" value.'))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Gender", tracking=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
        ('annulled', 'Annulled')
    ], string='Marital Status', tracking=True)
    mobile = fields.Char(string="Primary Mobile No.")
    mobile2 = fields.Char(string="Secondary Mobile No.")
    phone = fields.Char(string="Landline No.")
    religion_id = fields.Many2one('res.partner.religion', string="Religion")
    nationality_country_id = fields.Many2one('res.country', string="Nationality")
    employment_status_id = fields.Many2one('res.partner.employment.status', string="Employment Status", help="Class Code")
    employment_country_id = fields.Many2one('res.country', string="Employment Country")
    profession_id = fields.Many2one('res.partner.profession', string="Profession")
    age = fields.Integer(string="Age", readonly=True)
    age_range_id = fields.Many2one('res.partner.age.range', string="Age Range")
    monthly_income_range_id = fields.Many2one('res.partner.monthly.income.range', string="Monthly Income Range")
    monthly_income = fields.Float('Monthly Income')
    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_github = fields.Char('GitHub Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')
    social_instagram = fields.Char('Instagram Account')

    @api.model
    def create(self, vals):
        if vals.get('date_of_birth'):
            # _logger.info(f"\n\n{datetime.strptime(vals.get('date_of_birth'), '%Y-%m-%d')}\n\n")
            age = date.today().year - datetime.strptime(vals.get('date_of_birth'), "%Y-%m-%d").year
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            vals.update({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False

            })
        if vals.get('monthly_income'):
            income_range = self.env['res.partner.monthly.income.range'].search(
                [('range_from', '<=', vals.get('monthly_income')), ('range_to', '>=', vals.get('monthly_income'))], limit=1)
            vals['monthly_income_range_id'] = income_range[:1] and income_range.id or False
        return super(ResPartner, self).create(vals)

    def split_date(self, date):
        """
        Method to split a date into year,month,day separatedly
        @param date date:
        """
        year = date.year
        month = date.month
        day = date.day
        return year, month, day

    def write(self, vals):
        if 'date_of_birth' in vals and vals.get('date_of_birth'):
            age = date.today().year - datetime.strptime(vals.get('date_of_birth'), "%Y-%m-%d").year
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            vals.update({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False

            })
        if vals.get('monthly_income'):
            income_range = self.env['res.partner.monthly.income.range'].search(
                [('range_from', '<=', vals.get('monthly_income')), ('range_to', '>=', vals.get('monthly_income'))], limit=1)
            vals['monthly_income_range_id'] = income_range[:1] and income_range.id or False
        return super(ResPartner, self).write(vals)

    def cron_compute_age(self):
        current_year, current_month, current_day = self.split_date(date.today())
        partner = self.search([
            ('mob', '=', current_month),
            ('dyob', '=', current_day)
        ])
        for i in partner:
            age = date.today().year - i.date_of_birth.year
            _logger.info(f"\n\nAGE: {age}\n\n")
            age_range = self.env['res.partner.age.range'].search(
                [('range_from', '<=', age), ('range_to', '>=', age)], limit=1)
            i.write({
                'age': age,
                'age_range_id': age_range[:1] and age_range.id or False
            })
