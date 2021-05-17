# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger("_name_")


class PropertySaleSOAOverdueLine(models.Model):
    _name = 'property.sale.soa.overdue.line'
    _description = "SOA Overdues breakdown"
    _order = 'bill_date desc'
    _rec_name = 'bill_number'

    bill_number = fields.Char(string="Billing Number")
    bill_date = fields.Date(string="Billing Due Date", required=True)
    soa_number = fields.Char(string="SOA Number", required=True)
    soa_id = fields.Many2one('property.sale.statement.of.account', string="SOA", ondelete='cascade',
                             compute="_get_soa", inverse="_inverse_get_soa", store=True)
    customer_number = fields.Char(string="Customer #")
    so_number = fields.Char(string="SO #")
    billing_amount = fields.Float(string="Billing Amount")
    penalty = fields.Float(string="Penalty", commpute="_compute_penalty", inverse="_inverse_compute_penalty", store=True)
    amount_due = fields.Float(string="Amount Due", compute="_get_amount_due")

    @api.onchange('soa_number')
    def onchange_soa_number(self):
        if self.soa_number:
            soa = self.env['property.sale.statement.of.account'].sudo().search([('soa_number', '=', self.soa_number)], limit=1)
            if soa[:1]:
                self.soa_id = soa.id
                self.customer_number = soa.customer_number

    @api.model
    def create(self, vals):
        res = super(PropertySaleSOAOverdueLine, self).create(vals)
        res.onchange_soa_number()
        return res

    @api.depends('billing_amount')
    def _compute_penalty(self):
        for r in self:
            r.penalty = r.billing_amount * 0.04

    def _inverse_compute_penalty(self):
        for r in self:
            continue

    @api.onchange('soa_id')
    def onchange_soa_id(self):
        if self.soa_id:
            self.soa_number = self.soa_id.soa_number
            self.so_number = self.soa_id.so_number
            self.customer_number = self.soa_id.customer_number

    @api.depends('soa_number')
    def _get_soa(self):
        soa = self.env['property.sale.statement.of.account']
        for r in self:
            soa_rec = soa.sudo().search([('soa_number', '=', r.soa_number)], limit=1)
            r.soa_id = soa_rec[:1] and soa_rec.id or False

    def _inverse_get_soa(self):
        for r in self:
            continue

    @api.depends('billing_amount', 'penalty')
    def _get_amount_due(self):
        for r in self:
            r.amount_due = sum([r.billing_amount, r.penalty])


class PropertySaleStatementOfAccount(models.Model):
    _name = 'property.sale.statement.of.account'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Statement of Account"
    _order = 'soa_date desc'
    _rec_name = 'soa_number'

    _sql_constraints = [
        ('soa_number_key', 'unique(soa_number, company_code)', "Duplicate of SOA Number is not allowed in the same company!")
    ]

    customer_number = fields.Char(string="Customer #", index=True, track_visibility="always")
    so_number = fields.Char(string="SO #", required=True, track_visibility="always")
    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale")
    company_code = fields.Char(string="Company Code", track_visibility="always")
    partner_id = fields.Many2one('res.partner', string="Customer", store=True, compute="_get_contact_details")
    company_id = fields.Many2one('res.company', 'Company', index=True,
                                 store=True, compute="_get_contact_details", check_company=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id", store=True)
    be_code = fields.Char(string="BE Code", help="Business Entity Code", track_visibility="always")
    block_lot = fields.Char(string="Block-Lot", track_visibility="always")
    su_number = fields.Char(string="SU Number", track_visibility="always")
    property_id = fields.Many2one('property.detail', string="Property", store=True, compute='_get_property_detail',
                                  inverse='_inverse_get_property_detail')
    soa_number = fields.Char(string="SOA Number", required=True, track_visibility="always", index=True)
    date_generated = fields.Date(string="Date Generated")
    soa_date = fields.Date(string="SOA Date", required=True, track_visibility="always")
    soa_month = fields.Integer(string="Month", compute='_get_date_parsed', store=True)
    soa_year = fields.Integer(string="Year", compute='_get_date_parsed', store=True)
    soa_due_date = fields.Date(string="Due Date", required=True, track_visibility="always")
    current_amount = fields.Float(string="Current Amount Dues", track_visibility="always")
    penalty = fields.Float(string="Penalty")
    past_due = fields.Float(string="Past Dues")
    past_due_count = fields.Integer(string="Past Due Count")
    past_due_line_ids = fields.One2many('property.sale.soa.overdue.line', 'soa_id', string="Past Due Breakdown")
    total_amount_due = fields.Float(string="Total Amount Due", compute='_get_total_amount_due', store=True)
    accrued_interest = fields.Float(string="Accrued Interest")
    account_officer_code1 = fields.Char(string="Account Officer 1 Code")
    account_officer_code2 = fields.Char(string="Account Officer 2 Code")
    account_officer_name1 = fields.Char(string="Account Officer 1 Name")
    account_officer_name2 = fields.Char(string="Account Officer 2 Name")
    account_officer_department1 = fields.Char(string="Account Officer 1 Department")
    account_officer_department2 = fields.Char(string="Account Officer 2 Department")
    account_officer_contact1 = fields.Char(string="Account Officer 1 Contact")
    account_officer_contact2 = fields.Char(string="Account Officer 2 Contact")
    unpaid_months = fields.Float(string="Unpaid Months", default=0)

    @api.depends('customer_number', 'company_code')
    def _get_contact_details(self):
        partner = self.env['res.partner']
        company = self.env['res.company']
        for r in self:
            if r.customer_number:
                contact = partner.sudo().search([('partner_assign_number', '=', r.customer_number)])
                r.partner_id = contact[:1] and contact.id or False
            if r.company_code:
                rec = company.sudo().search([('code', '=', r.company_code)], limit=1)
                r.company_id = rec[:1] and rec.id or False

    # @api.depends('so_number')
    # def _get_property_sale_details(self):
    #     property_sale = self.env['property.admin.sale']
    #     for r in self:
    #         property_sale_rec = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
    #         r.property_sale_id = property_sale_rec[:1] and property_sale_rec.id or False

    @api.onchange('so_number')
    def onchange_so_number(self):
        property_sale = self.env['property.admin.sale'].sudo().search([('so_number', '=', self.so_number)], limit=1)
        if property_sale[:1]:
            self.property_sale_id = property_sale.id
            self.partner_id = property_sale.partner_id.id
            self.customer_number = property_sale.customer_number
            self.company_id = property_sale.company_id.id
            self.company_code = property_sale.company_code
            self.be_code = property_sale.be_code
            self.block_lot = property_sale.block_lot
            self.su_number = property_sale.su_number

    @api.model
    def create(self, vals):
        res = super(PropertySaleStatementOfAccount, self).create(vals)
        res.onchange_so_number()
        if res.property_sale_id.subdivision_phase_id.auto_send_soa:
            email_temp = self.env.ref('property_admin_monitoring.email_template_statement_of_account')
            res.message_post_with_template(email_temp.id)
        return res

    # @api.depends('past_due_line_ids', 'past_due_line_ids.amount_due', 'past_due_line_ids.penalty')
    # def _get_total_past_dues(self):
    #     for i in self:
    #         total = 0
    #         penalty = 0
    #         count = 0
    #         for r in i.past_due_line_ids:
    #             total += r.billing_amount
    #             penalty += r.penalty
    #             count += 1
    #         i.past_due = total
    #         i.penalty = penalty
    #         i.past_due_count = count

    @api.depends('soa_date')
    def _get_date_parsed(self):
        for r in self:
            r.soa_month = r.soa_date.month
            r.soa_year = r.soa_date.year

    @api.depends('past_due', 'penalty', 'current_amount')
    def _get_total_amount_due(self):
        for r in self:
            r.total_amount_due = sum([r.past_due, r.penalty, r.current_amount])
    #
    # @api.constrains('partner_id', 'company_id')
    # def _validate_contact(self):
    #     if not self.partner_id:
    #         raise ValidationError(_(f"No Customer # {self.customer_number} in the customer database."))
    #     if not self.company_id:
    #         raise ValidationError(_(f"There is no such Company Code {self.company_code} in the database."))

    @api.depends('be_code', 'block_lot', 'su_number')
    def _get_property_detail(self):
        for r in self:
            if r.be_code and r.block_lot and r.su_number:
                property = self.env['property.detail'].search(
                    [('be_code', '=', r.be_code), ('block_lot', '=', r.block_lot), ('su_number', '=', r.su_number)],
                    limit=1)
                if property[:1]:
                    r.property_id = property.id

    def _inverse_get_property_detail(self):
        for r in self:
            continue


class PropertyLedgerPaymentItem(models.Model):
    _name = 'property.ledger.payment.item'
    _description = 'Payments Line Items related to SO'
    _check_company_auto = True
    _rec_name = 'or_number'
    _order = 'line_counter'

    line_counter = fields.Integer(string="Line Item Counter")
    customer_number = fields.Char(string="Customer #")
    so_number = fields.Char(string="SO #", required=True)
    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale")
    so_assign_number = fields.Char(string="Assignment #", help="SO Number sa SAP financial side")
    partner_id = fields.Many2one('res.partner', string="Customer", store=True, compute="_get_contact_details")
    company_code = fields.Char(string="Company Code")
    company_id = fields.Many2one('res.company', 'Company', index=True,
                                 store=True, compute="_get_contact_details", check_company=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    billing_number = fields.Char(string="Document #", help="Accounting Document Number")
    accounting_date = fields.Date(string="Document Date")
    posting_date = fields.Date(string="Posting Date")
    fiscal_year = fields.Char(string="Fiscal Year")
    document_type = fields.Selection([
                ('AA', 'Asset Posting'),
                ('AB', 'Accounting Document'),
                ('AC', 'Accrual Entry'),
                ('AD', 'Advance Commission'),
                ('AE', 'Advances to Employee'),
                ('AF', 'Dep. Postings'),
                ('AN', 'Net Asset Posting'),
                ('AU', 'Audit Adjustments'),
                ('BB', 'Buy Back Transaction'),
                ('BC', 'Brokers Com.Payable'),
                ('BK', 'Bank Recon(Dummy)'),
                ('BR', 'Billing / Payment Req'),
                ('CC', 'Cancel.of Cont Acct'),
                ('CD', 'Uncontracted'),
                ('CH', 'Contract settlement'),
                ('CM', 'Contractor Mgt.'),
                ('CN', 'Credit Note'),
                ('CO', 'Controlling Document'),
                ('CP', 'Amort - Cap.Principal'),
                ('CT', 'Commercial Trans'),
                ('DA', 'Customer Document'),
                ('DG', 'Customer Credit Memo'),
                ('DN', 'Intercompany Posting'),
                ('DR', 'Customer invoice'),
                ('DZ', 'Customer payment'),
                ('EU', 'Euro Rounding Diff.'),
                ('EX', 'External number'),
                ('FC', 'Amort - Interest'),
                ('HC', 'House Construction'),
                ('HI', 'HI Reclass'),
                ('HR', 'House Repair'),
                ('IA', 'Inventory Adjustment'),
                ('IS', 'Inventory Set up'),
                ('JI', 'JV - Interest'),
                ('JV', 'Joint Venture'),
                ('KA', 'Vendor document'),
                ('KG', 'Vendor Credit Memo'),
                ('KN', 'Net Vendors'),
                ('KP', 'Account Maintenance'),
                ('KR', 'Vendor Invoice'),
                ('KZ', 'Vendor Payment'),
                ('LD', 'Land Development'),
                ('LR', 'Loan Release'),
                ('LT', 'Contracted - ST'),
                ('ML', 'ML Settlement'),
                ('PB', 'Promo Buyer'),
                ('PC', 'PagIbig Collection'),
                ('PG', 'Pag - ibig Remittance'),
                ('PL', 'Payroll Liquidation'),
                ('PO', 'POC Adjustment'),
                ('PP', 'Prepayment'),
                ('PR', 'Price change'),
                ('PV', 'Provisional Receipt'),
                ('PY', 'Prior - Year Adj.'),
                ('RA', 'Sub.cred.memo stlmt'),
                ('RB', 'Reserve for Bad Debt'),
                ('RE', 'Invoice - gross'),
                ('RJ', 'Recurring Journals'),
                ('RL', 'Rev.of Aud.Adjstmnts'),
                ('RN', 'Invoice - Net'),
                ('RV', 'Billing Doc. Transfer'),
                ('SA', 'G / L Account Document'),
                ('SB', 'G / L Account Posting'),
                ('SD', 'Sales Discount'),
                ('SJ', 'SR - JV Project'),
                ('SK', 'Cash Document'),
                ('SL', 'Sub to Liquidation'),
                ('SR', 'SR - Owned Project'),
                ('ST', 'Contracted - ST'),
                ('SU', 'Adjustment document'),
                ('TP', 'Transfer Payments'),
                ('TR', 'Transfer Payment'),
                ('UC', 'Cancel of Uncon Acct'),
                ('UE', 'Data Transfer'),
                ('UI', 'Uncont - Interest'),
                ('VD', 'Variation Order Inc.'),
                ('VI', 'Variation Order Inc.'),
                ('WA', 'Goods Issue'),
                ('WE', 'Goods Receipt'),
                ('WI', 'Inventory Document'),
                ('WL', 'Goods Issue / Delivery'),
                ('WN', 'Net Goods Receipt'),
                ('ZJ', 'Cash Document'),
                ('ZL', 'Legacy Data Transfer'),
                ('ZP', 'Payment Posting'),
                ('ZR', 'Bank Reconciliation'),
                ('ZS', 'Payment by Check'),
                ('ZV', 'Payment Clearing'),
                ('ZZ', 'Capitalized Principal')
            ], string="Document Type")
    billing_date = fields.Date(string="Billing Date")
    billing_amount = fields.Monetary(string="Billing Amount")
    billing_type = fields.Selection([
                ('ZB01', 'Uncontracted'),
                ('ZB02', 'Contracted Short Trm'),
                ('ZB03', 'Contracted Long Term'),
                ('ZB04', 'Capitalized Interest'),
                ('ZB05', 'Capitalized Principal'),
                ('ZB06', 'Interest'),
                ('ZB07', 'Uncon Interest'),
                ('ZB08', 'JV Principal'),
                ('ZB09', 'JV Interest'),
                ('ZG21', 'CM Uncontracted'),
                ('ZG22', 'CM Short Term'),
                ('ZG23', 'CM Long Term'),
                ('ZG24', 'CM Cap.Interest'),
                ('ZG25', 'CM Cap.Principal'),
                ('ZG26', 'CM Interest'),
                ('ZG27', 'CM Uncon Interest'),
                ('ZG28', 'CM JV Principal'),
                ('ZG29', 'CM JV Interest')
            ], string="Billing Type")
    billing_due_date = fields.Date(string="Baseline Date", help="Billing due date in the Financial side")
    customer_notes = fields.Char(string="Customer Notes", help="Item Text for Customer Line Item")
    principal_amount = fields.Monetary(string="Principal Amount")
    sundry_amount = fields.Monetary(string="Sundry Amount")
    interest_amount = fields.Monetary(string="Interest Rate Amount")
    total_amount = fields.Monetary(string="Total Amount", store=True, compute='_get_total_amount')
    or_number = fields.Char(string="OR Number")
    payment_document_number = fields.Char(string="Payment Document Number")
    transaction_description = fields.Text(string="Transaction Description")
    payment_amount = fields.Monetary(string="Payment Amount")
    bank_notes = fields.Char(string="Mode of Payment", help="Item Text for Bank Line item")
    payment_posting_date = fields.Date(string="Payment Posting Date")
    reference_document_number = fields.Char(string="Reference Document Number")
    reference_number = fields.Char(string="Reference Number")
    reference_count = fields.Char(string="Reference Count")
    recap_amount = fields.Monetary(string="Recap Amount")
    restructure_amount = fields.Monetary(string="Restructure Amount")
    unpaid_amount = fields.Monetary(string="Unpaid Amount")
    running_bal = fields.Float(string="Running Balance", help="SAP: RUNBAL")
    clearing_document_ref = fields.Char("Clearing Reference", help="Document Number of the clearing document (SAP: AUGBL)")
    clearing_date = fields.Date(string="Clearing Date", help="SAP: AUGDT")
    allocated_to_requirement = fields.Char(string="Receipt is Allocated to Requirement", help="SAP: ALLOC")
    line_tagging = fields.Char("Line Display Tagging", help="SAP: TAG")
    amount_in_local_currency = fields.Float(string="Amount in Local Currency", help="SAP: DBTR")

    @api.depends('principal_amount', 'sundry_amount', 'interest_amount')
    def _get_total_amount(self):
        for r in self:
            r.total_amount = sum([r.principal_amount, r.sundry_amount, r.interest_amount])

    @api.onchange('so_number')
    def onchange_so_number(self):
        property_sale = self.env['property.admin.sale'].sudo().search([('so_number', '=', self.so_number)], limit=1)
        if property_sale[:1]:
            self.property_sale_id = property_sale.id
            self.partner_id = property_sale.partner_id.id
            self.customer_number = property_sale.customer_number
            self.company_id = property_sale.company_id.id
            self.company_code = property_sale.company_code

    @api.model
    def create(self, vals):
        res = super(PropertyLedgerPaymentItem, self).create(vals)
        res.onchange_so_number()
        return res

    # @api.depends('so_number')
    # def _get_property_sale_details(self):
    #     property_sale = self.env['property.admin.sale']
    #     for r in self:
    #         property_sale_rec = property_sale.sudo().search([('so_number', '=', r.so_number)], limit=1)
    #         r.property_sale_id = property_sale_rec[:1] and property_sale_rec.id or False

    @api.depends('customer_number', 'company_code')
    def _get_contact_details(self):
        partner = self.env['res.partner']
        company = self.env['res.company']
        for r in self:
            if r.customer_number:
                contact = partner.sudo().search([('partner_assign_number', '=', r.customer_number)])
                r.partner_id = contact[:1] and contact.id or False
            if r.company_code:
                rec = company.sudo().search([('code', '=', r.company_code)], limit=1)
                r.company_id = rec[:1] and rec.id or False

    # @api.constrains('partner_id', 'company_id')
    # def _validate_contact(self):
    #     if not self.partner_id:
    #         raise ValidationError(_(f"No Customer # {self.customer_number} in the customer database."))
    #     if not self.company_id:
    #         raise ValidationError(_(f"There is no such Company Code {self.company_code} in the database."))

