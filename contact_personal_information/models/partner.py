# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from dateutil.parser import parse
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
        ('other', 'Other'),
        ('unspecified', 'Unspecified')
    ], string="Gender", defualt="unspecified", tracking=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
        ('annulled', 'Annulled'),
        ('unspecified', 'Unspecified')
    ], string='Marital Status', defualt="unspecified", tracking=True)
    mobile = fields.Char(string="Primary Mobile No.")
    mobile2 = fields.Char(string="Secondary Mobile No.")
    phone = fields.Char(string="Landline No.")
    religion_id = fields.Many2one('res.partner.religion', string="Religion")
    nationality_country_id = fields.Many2one('res.country', string="Nationality")
    employment_status_id = fields.Many2one('res.partner.employment.status', string="Employment Type", help="Class Code")
    employment_country_id = fields.Many2one('res.country', string="Employment Country")
    profession_id = fields.Many2one('res.partner.profession', string="Profession")
    age = fields.Integer(string="Age", readonly=True)
    age_range_id = fields.Many2one('res.partner.age.range', string="Age Range")
    monthly_income_range_id = fields.Many2one('res.partner.monthly.income.range', string="Monthly Income Range")
    monthly_income = fields.Float('Monthly Income')
    income_currency_id = fields.Many2one('res.currency', string="Income Currency")
    income_currency_code = fields.Char(string="Income Currency Code")
    social_twitter = fields.Char('Twitter Account')
    social_facebook = fields.Char('Facebook Account')
    social_github = fields.Char('GitHub Account')
    social_linkedin = fields.Char('LinkedIn Account')
    social_youtube = fields.Char('Youtube Account')
    social_instagram = fields.Char('Instagram Account')

    @api.onchange('income_currency_id')
    def onchange_currency_id(self):
        if self.income_currency_id:
            self.income_currency_code = self.income_currency_id.name

    def is_valid_date(self, date):
        if date:
            try:
                parse(date)
                return True
            except:
                return False
        return False

    @api.onchange('income_currency_code')
    def onchange_currency_code(self):
        if self.income_currency_code:
            currency = self.env['res.currency'].sudo().search([('name', '=', self.income_currency_code)])
            self.income_currency_id = currency[:1] and currency.id or self.company_id.currency_id

    @api.model
    def create(self, vals):
        if vals.get('date_of_birth'):
            if not self.is_valid_date(vals.get('date_of_birth')):
                vals['date_of_birth'] = False
            # _logger.info(f"\n\n{datetime.strptime(vals.get('date_of_birth'), '%Y-%m-%d')}\n\n")
            age = int((datetime.now() - datetime.strptime(vals.get('date_of_birth'), "%Y-%m-%d")).days / 365.25)
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
        res = super(ResPartner, self).create(vals)
        res.onchange_currency_code()
        return res

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
            age = int((datetime.now() - datetime.strptime(vals.get('date_of_birth'), "%Y-%m-%d")).days / 365.25)
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
