# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
from odoo.osv import expression
import http
import json

import urllib.request
import urllib.parse
import logging

_logger = logging.getLogger("_name_")

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class PropertyFinancingTypeTerm(models.Model):
    _name = "property.financing.type.term"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Financing Term'

    active = fields.Boolean(default=True)
    financing_type_id = fields.Many2one('property.financing.type', string="Financing Type")
    name = fields.Char(string="Display Name", store=True, compute="_get_name")
    year = fields.Integer(string="Years", help="Number of Years to Pay", track_visibility="always")
    interest_rate = fields.Float(string="Interest Rate (%)", track_visibility="always")

    @api.depends('year', 'interest_rate')
    def _get_name(self):
        for i in self:
            if i.year and i.interest_rate:
                i.name = f"{i.year}YEARS @ {i.interest_rate}% INTEREST"


class PropertyFinancingType(models.Model):
    _name = "property.financing.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Financing Type'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Financing Type", required=True, track_visibility="always")
    code = fields.Char(string="Code", required=True, track_visibility="always")
    description = fields.Text(string="Description", track_visibility="always")
    financing_term_ids = fields.One2many('property.financing.type.term', 'financing_type_id',
                                         string="Payment Terms and Interest Rates")

    # payment_term_id = fields.Many2one('account.payment.term', string="Payment Term")

    def name_get(self):
        res = super(PropertyFinancingType, self).name_get()
        data = []
        for i in self:
            display_value = f"{i.name} [{i.code}]"
            data.append((i.id, display_value))
        return data

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', '|', ('code', operator, name), ('name', operator, name), ('description', operator, name)]
        return super(PropertyFinancingType, self).search(expression.AND([args, domain]), limit=limit).name_get()


class PropertyDownpaymentTerm(models.Model):
    _name = "property.downpayment.term"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Down payment Term'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Display Name", store=True, compute="_get_name")
    month = fields.Integer(string="Months", help="Number of Month to Pay", track_visibility="always")
    interest_rate = fields.Float(string="Interest Rate", track_visibility="always")

    @api.depends('month', 'interest_rate')
    def _get_name(self):
        for i in self:
            i.name = f"{i.month}Months @ {i.interest_rate}% INTEREST"


class PropertySaleDownloadableDocument(models.Model):
    _name = 'property.sale.downloadable.document'
    _description = 'Downloadable Documents'
    _order = 'sequence'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Document", required=True)
    description = fields.Text(string="Document Description")
    sequence = fields.Integer(string="Sequence", default=10)
    attachment_file = fields.Binary(string="Attachment File")
    attachment_file_name = fields.Char("File Name")


class PropertySaleRequiredDocument(models.Model):
    _name = 'property.sale.required.document'
    _description = 'Required Documents in sales Transaction'
    _order = 'sequence'

    active = fields.Boolean(default=True)
    code = fields.Char(string="Code", required=True)
    group_code = fields.Char(string="Group Code", required=True)
    name = fields.Char(string="Document", required=True)
    description = fields.Text(string="Document Description", help="Customer Portal Document Document Purpose")
    note = fields.Text(string="Notes",
                       help="Customer Portal Document Note Purpose like when the document should be required.")
    employment_status_id = fields.Many2one('res.partner.employment.status', string="Employment Type",
                                           help="Required For Employment type Documents")
    optional_requirement = fields.Boolean(string="Optional")
    sequence = fields.Integer(string="Sequence", default=10)
    preview_file = fields.Binary(string="Preview File", help="Customer Portal Document preview Purpose")
    submitted_by_buyer = fields.Boolean(string="Submitted By Buyer")
    preview_file_name = fields.Char(string="Preview File Name")

    def name_get(self):
        res = []
        for rec in self:
            if rec.optional_requirement:
                res.append((rec.id, f"{rec.name} (Optional)"))
            else:
                res.append((rec.id, f"{rec.name}"))
        return res


class PropertySaleCancellationReason(models.Model):
    _name = 'property.sale.cancellation.reason'
    _description = "Cancellation Reasons"

    active = fields.Boolean(default=True)
    code = fields.Char(string="Code")
    name = fields.Char(string="Reason", required=True)
    description = fields.Text(string="Description")


class PropertyStatusAssignedPerson(models.Model):
    _name = 'property.status.assigned.person'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Assigned person on each sale status and Project"
    _sql_constraints = [('subdivision_phase_id', 'unique(subdivision_phase_id, state_id)',
                         'You already have setup for this Project and Sales Status')]

    state_id = fields.Many2one('property.sale.status', string="Sale Status")
    account_officer_user_id = fields.Many2one('res.users', string="Account Officer",
                                              help="Sales Admin Account Officer Assigned", track_visibility="always")
    collection_officer_user_id = fields.Many2one('res.users', string="Collection Officer",
                                                 help="Collection Account Officer Assigned", track_visibility="always")
    subdivision_phase_id = fields.Many2one('property.subdivision.phase', string="Project", required=True, copy=False)
    be_code = fields.Char(string="BE Code", store=True, related="subdivision_phase_id.be_code")
    brand = fields.Char(string="brand", store=True, related="subdivision_phase_id.brand")


class PropertySaleDocumentStatusBrand(models.Model):
    _name = 'property.sale.document.status.project'
    _description = "Document specific Per Project Only"
    _sql_constraints = [('subdivision_phase_id', 'unique(subdivision_phase_id, state_id)',
                         'You already have setup for this Project and Sales Status')]

    state_id = fields.Many2one('property.sale.status', string="Sale Status")
    subdivision_phase_id = fields.Many2one('property.subdivision.phase', string="Project", required=True, copy=False)
    be_code = fields.Char(string="BE Code", store=True, related="subdivision_phase_id.be_code")
    brand = fields.Char(string="brand", store=True, related="subdivision_phase_id.brand")
    required_sale_document_requirement_ids = fields.Many2many('property.sale.required.document',
                                                              'property_sale_status_document_project_rel',
                                                              string="Documents",
                                                              track_visibility="always")


class PropertySaleStatus(models.Model):
    _name = 'property.sale.status'
    _description = 'Property Sales Monitoring Status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc'

    name = fields.Char(string="Status", required=True, track_visibility="always")
    sequence = fields.Integer(string="Sequence", default=10, track_visibility="always")
    active = fields.Boolean(default=True)
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')
    required_sale_document_requirement_ids = fields.Many2many('property.sale.required.document',
                                                              'property_sale_status_document_rel',
                                                              string="Global Document Requirements",
                                                              help="Document that are not brand specific",
                                                              track_visibility="always")
    project_specific_document_ids = fields.One2many('property.sale.document.status.project', 'state_id',
                                                    string="Project Specific Document Requirement")
    predecessor_stage_id = fields.Many2one('property.sale.status', string="Predecessor Stage")
    project_assigned_person_ids = fields.One2many('property.status.assigned.person', 'state_id',
                                                  string="Assigned Persons")
    with_predecessor = fields.Boolean(string="With Predecessor Stage", default=True)
    successor_stage_id = fields.Many2one('property.sale.status', string="Successor Stage")
    with_successor = fields.Boolean(string="With Successor Stage", default=True)
    canceled = fields.Boolean(string="Cancelled Stage")
    allowed_edit_delete_name = fields.Boolean("Allowed Edit and Delete")
    document_submission_days = fields.Integer(string="Document Submission Due In")
    document_submission_reminder = fields.Integer(string="Document Submission Reminder")

    # def write(self, vals):
    #     if self.allowed_edit_delete_name and vals.get('name'):
    #         vals.pop('name')
    #     return super(PropertySaleStatus, self).write(vals)

    def unlink(self):
        for r in self:
            raise ValidationError(
                _("This Record is not allowed to be deleted. Some backend programs are referencing to this record."))


class PropertySaleStatus(models.Model):
    _name = 'property.sale.sub.status'
    _description = 'Property Sales Monitoring Sub-Status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc'

    name = fields.Char(string="Sub-status", required=True, track_visibility="always")
    sub_parent_id = fields.Many2one('property.sale.status', string="Parent Status", required=True,
                                    track_visibility="always")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
    trigger_admin_qualified = fields.Boolean(string="Trigger as Admin Qualified")
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')
    required_sale_document_requirement_ids = fields.Many2many('property.sale.required.document',
                                                              'property_sale_parent_status_document_rel', store=True,
                                                              string="Required Document",
                                                              compute='_get_parent_document')
    required_sub_sale_document_requirement_ids = fields.Many2many('property.sale.required.document',
                                                                  'property_sale_sub_status_document_rel',
                                                                  string="Required Document", track_visibility="always",
                                                                  domain="[('id', 'in', required_sale_document_requirement_ids)]")
    predecessor_stage_id = fields.Many2one('property.sale.sub.status', string="Predecessor Stage")
    with_predecessor = fields.Boolean(string="With Predecessor Stage", default=True)
    successor_stage_id = fields.Many2one('property.sale.sub.status', string="Successor Stage")
    with_successor = fields.Boolean(string="With Successor Stage", default=True)
    canceled = fields.Boolean(string="Canceled Stage")

    @api.depends('sub_parent_id', 'sub_parent_id.required_sale_document_requirement_ids')
    def _get_parent_document(self):
        for r in self:
            if r.sub_parent_id:
                r.required_sub_sale_document_requirement_ids = r.sub_parent_id.required_sale_document_requirement_ids.ids


class PropertySaleBankLoanApplication(models.Model):
    _name = 'property.sale.bank.loan.application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Bank Loan Application Line'
    _rec_name = 'bank_id'
    _order = 'submission_date desc'

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company, check_company=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale", track_visibility="always",
                                       domain="[('company_id', 'child_of', [company_id])]")
    bank_id = fields.Many2one('res.bank', string="Bank", required=True, track_visibility="always")
    desired_loan_amount = fields.Monetary(string="Desired Loan Amount", required=True, track_visibility="always")
    approved_loan_amount = fields.Monetary(string="Approve Amount", track_visibility="always")
    bank_fee = fields.Monetary(string="Bank Fee", track_visibility="always")
    net_proceeds = fields.Monetary(string="Net Proceeds", track_visibility="always")
    approved_date = fields.Date(string="Approved Date", track_visibility="always")
    valid_until = fields.Date(string="Valid Until", track_visibility="always")
    declined_date = fields.Date(string="Declined Date", track_visibility="always")
    declined_reason = fields.Text(string="Declined Reason", track_visibility="always")
    submission_date = fields.Date(string="Submission Date", track_visibility="always")
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('processing', 'Processing'),
                              ('approved', 'Approved'),
                              ('declined', 'Declined'),
                              ('canceled', 'Canceled')],
                             string="State", default='draft', track_visibility="always")


class PropertyInspection(models.Model):
    _name = 'property.inspection'
    _description = 'Property Description'
    _rec_name = 'property_sale_id'

    property_sale_id = fields.Many2one('property.admin.sale', string="Property Sale")
    inspection_date = fields.Date('Date', required=True)
    feedback = fields.Text(string="Feedback", required=True)
    passed = fields.Boolean(string="Passed")
    failed_remark = fields.Text(string="Failed Remark")


class PropertyAdminSale(models.Model):
    _name = 'property.admin.sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Admin Sales Monitoring'

    _sql_constraints = [
        ('so_number_be_code_key', 'unique(so_number, company_code)',
         "Duplicate of SO Number is not allowed in the same company!")
    ]

    @api.model
    def _get_default_stage(self):
        stage = self.env['property.sale.status'].search([('active', '=', True)], order='sequence asc')
        if not stage[:1]:
            raise ValidationError(_("Please setup sales stages first"))
        return stage[0].id

    # @api.model
    # def _get_default_sub_stage(self):
    #     stage = self.env['property.sale.status'].search([('active', '=', True)], order='sequence asc')
    #     if not stage[:1]:
    #         raise ValidationError(_("Please setup sales stages first"))
    #     sub_stage = self.env['property.sale.sub.status'].search(
    #         [('active', '=', True), ('sub_parent_id', '=', stage[0].id)], order='sequence asc')
    #     if not sub_stage[:1]:
    #         return False
    #     return sub_stage[0].id

    @api.depends('so_number', 'property_id', 'property_id.block_lot', 'property_id.su_number')
    def _get_display_name(self):
        for i in self:
            if i.su_number and i.block_lot:
                i.name = f"{i.so_number}_{i.block_lot}"

    def _get_payment_lines(self):
        payment = self.env['property.ledger.payment.item']
        for r in self:
            principal = 0
            interest = 0
            penalty = 0
            payment_history = payment.sudo().search([('so_number', '=', r.so_number)])
            r.payment_history_ids = payment_history
            for i in payment_history:
                principal += i.principal_amount
                interest += i.interest_amount
                penalty += i.sundry_amount
            r.total_penalty_paid = penalty
            r.total_principal_amount_paid = principal
            r.total_interest_amount_paid = interest
            r.grand_total_paid = sum([penalty, interest, principal])
            r.outstanding_balance = r.tcp - principal

    def _get_soa_lines(self):
        soa = self.env['property.sale.statement.of.account']
        for r in self:
            r.soa_history_ids = soa.sudo().search([('so_number', '=', r.so_number)])

    moved_stage_datetime = fields.Datetime(string="Date Moved to Current Stage", readonly=True)
    moved_sub_stage_datetime = fields.Datetime(string="Date Moved to Current Sub_Stage", readonly=True)
    stage_age = fields.Float(string="Stage Aging", readonly=True)
    sub_stage_age = fields.Float(string="Sub-Stage Aging", readonly=True)
    status_log_ids = fields.One2many('property.sale.status.log', 'property_sale_id', readonly=True, force_save=True)
    assignment_log_ids = fields.One2many('property.sale.assignment.log', 'property_sale_id', readonly=True,
                                         force_save=True)
    stage_id = fields.Many2one('property.sale.status', string="Status", group_expand='_expand_stages',
                               default=_get_default_stage, track_visibility="always")
    sub_stage_id = fields.Many2one('property.sale.sub.status', string="Sub-Status", track_visibility="always")
    account_officer_user_id = fields.Many2one('res.users', string="Account Officer",
                                              help="Sales Admin Account Officer Assigned", track_visibility="always")
    ao_assigned_date = fields.Date(string="Account Officer Assigned Date", track_visibility="always")
    collection_officer_user_id = fields.Many2one('res.users', string="Collection Officer",
                                                 help="Collection Account Officer Assigned", track_visibility="always")
    co_assigned_date = fields.Date(string="Collection Officer Assigned Date", track_visibility="always")
    first_letter = fields.Boolean(string="1st Letter", help="Demand To Pay", track_visibility="always")
    first_letter_sent = fields.Date(string="1st Sent", help="Demand To Pay", track_visibility="always")
    first_letter_received = fields.Date(string="1st Received By Customer", help="Demand To Pay",
                                        track_visibility="always")
    second_letter = fields.Boolean(string="2nd Letter", help="Notice of Delinquency and Cancellation",
                                   track_visibility="always")
    second_letter_sent = fields.Date(string="2nd Sent", help="Notice of Delinquency and Cancellation",
                                     track_visibility="always")
    second_letter_received = fields.Date(string="2nd Received By Customer",
                                         help="Notice of Delinquency and Cancellation",
                                         track_visibility="always")
    third_letter = fields.Boolean(string="3rd Letter", help="Demand to Vacate/Notice of Takeover",
                                  track_visibility="always")
    third_letter_sent = fields.Date(string="3rd Sent", help="Demand to Vacate/Notice of Takeover",
                                    track_visibility="always")
    third_letter_received = fields.Date(string="3rd Received By Customer", help="Demand to Vacate/Notice of Takeover",
                                        track_visibility="always")

    for_cancellation_user_id = fields.Many2one('res.users', string="Requested for Cancellation",
                                               track_visibility="always")
    for_cancellation = fields.Boolean("For Cancellation", track_visibility="always", readonly=True)
    for_cancellation_date = fields.Date("For Cancellation Date", help="Date requested for cancellation", readonly=True)
    cancellation_reason_id = fields.Many2one('property.sale.cancellation.reason', string="Cancellation Reason",
                                             readonly=True, track_visibility="always")
    cancellation_reason_code = fields.Char(string="Cancellation Reason Code", track_visibility="always")
    db_cancellation_tracker = fields.Integer(track_visibility="always")
    db_cancellation_log = fields.Text(track_visibility="always", readonly=True)
    cancellation_date = fields.Date("Cancellation Date", help="Date cancelled", readonly=True)
    before_cancelled_stage_id = fields.Many2one('property.sale.status', string="Account Last Stage",
                                                help="Account Stage before tagged as cancelled.", readonly=True)
    ready_for_contracted_sale = fields.Boolean(string="Ready For Contracted Sale", track_visibility="always",
                                               readonly=True)
    ready_for_contracted_sale_date = fields.Date(string="Ready For Contracted Sale Date", track_visibility="always",
                                                 readonly=True)
    db_for_contracted_sale_tracker = fields.Integer(track_visibility="always", readonly=True)
    db_for_contracted_sale_log = fields.Text(track_visibility="always", readonly=True)
    contracted_sale_date = fields.Date("CS Date", help="Date Moved to CS", readonly=True)
    for_contracted_sale_user_id = fields.Many2one('res.users', string="Requested for CS", track_visibility="always",
                                                  readonly=True)

    db_release_commission_tracker = fields.Integer(track_visibility="always", readonly=True)
    db_release_commission_log = fields.Text(track_visibility="always", readonly=True)
    released_commission = fields.Boolean(string="Released Advance Commission", track_visibility="always", readonly=True)
    request_released_commission = fields.Boolean(string="Requested Released Advance Commission",
                                                 track_visibility="always", readonly=True)

    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True, default=AVAILABLE_PRIORITIES[0][0])
    color = fields.Integer('Color Index', default=0)
    name = fields.Char(string="Document Reference", store=True, compute="_get_display_name")
    payment_history_ids = fields.Many2many('property.ledger.payment.item', 'so_payment_line_rel',
                                           compute="_get_payment_lines")
    soa_history_ids = fields.Many2many('property.sale.statement.of.account', 'sale_soa_rel', compute="_get_soa_lines")
    so_number = fields.Char(string="SO Number", required=True, track_visibility="always", index=True)
    so_date = fields.Date(string="SO Date", required=True, track_visibility="always")
    reservation_date = fields.Date(string="Original RS Date", track_visibility="always", help="Reservation Date")
    recontracted_one = fields.Boolean(string="Is Re-contracted (1)", track_visibility="always")
    recontracted_two = fields.Boolean(string="Is Re-contracted (2)", track_visibility="always")
    recontract_rs_date = fields.Date(string="Re-contract RS Date 1", track_visibility="always")
    recontracted_so_number = fields.Char(string="Re-contract SO 1", track_visibility="always")
    recontract_rs_date2 = fields.Date(string="Re-contract RS Date 2", track_visibility="always")
    recontracted_so_number2 = fields.Char(string="Re-contract SO 2", track_visibility="always")
    reactivated = fields.Boolean(string="Reactivated", track_visibility="always")
    reactivated_date = fields.Date(string="Reactivated Date", track_visibility="always")
    reactivated_reason = fields.Text(string="Reactivated Reason", track_visibility="always")
    buyback = fields.Boolean(string="Buyback", track_visibility="always")
    buyback_date = fields.Date(string="Reactivated Date", track_visibility="always")
    buyback_reason = fields.Text(string="Reactivated Reason", track_visibility="always")
    partner_id = fields.Many2one('res.partner', string="Customer", track_visibility="always")
    customer_number = fields.Char(string="Customer Number", required=True)
    employment_status_id = fields.Many2one('res.partner.employment.status', string="Employment Type", track_visibility="always")
    company_id = fields.Many2one('res.company', 'Company', index=True)
    company_code = fields.Char(string="Company Code")
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id")
    property_id = fields.Many2one('property.detail', string="Property")
    subdivision_phase_id = fields.Many2one('property.subdivision.phase', string="Project",
                                           related="property_id.subdivision_phase_id", store=True)
    house_model_id = fields.Many2one('housing.model', string="Unit/House Model", related="property_id.house_model_id",
                                     store=True)
    be_code = fields.Char(string="BE Code", help="Business Entity Code", required=True, track_visibility="always")
    brand = fields.Char(string="Brand", related="subdivision_phase_id.brand", store=True)
    su_number = fields.Char(string="SU Number", required=True, track_visibility="always")
    block_lot = fields.Char(string="Block-Lot", required=True, track_visibility="always")
    property_type = fields.Selection([
        ('Combo Condo Unit', 'Combo Condo Unit'),
        ('Condo Parking', 'Condo Parking'),
        ('Condo', 'Condo Only'),
        ('Combo House & Lot', 'Combo House & Lot'),
        ('House & Lot', 'House & Lot'),
        ('House Only', 'House Only'),
        ('Lot Only', 'Lot Only'),
        ('Combo Lot Only', 'Combo Lot Only'),
        ('unspecified', 'Unspecified')],
        string="Usage Type", defualt="unspecified", track_visibility="always")
    property_unit_state = fields.Selection([
        ('Ongoing', 'Ongoing'),
        ('NRFO', 'NRFO'),
        ('RFO', 'RFO'),
        ('Lot Only', 'Lot Only'),
        ('BTS', 'BTS')],
        string="House Unit Status", related="property_id.state", store=True)
    model_type_id = fields.Many2one("property.model.type", string="House Class",
                                    store=True, related="property_id.model_type_id")
    house_model_description = fields.Text(string="House Model Description", track_visibility="always")
    model_unit_type_id = fields.Many2one("property.model.unit.type", string="Unit Type (Depricated)",
                                         store=True, related="property_id.model_unit_type_id")
    house_series = fields.Char(string="House Series", store=True, related="property_id.unit_type")
    unit_type = fields.Char(string="Unit Type", store=True, related="property_id.unit_type")
    category = fields.Selection([('economic', 'Economic'), ('socialized', 'Socialized')], string="Series",
                                store=True, related="property_id.category")
    lot_area_price = fields.Monetary(string="Lot Area Price", track_visibility="always")
    floor_area_price = fields.Monetary(string="Floor Area Price", track_visibility="always")
    floor_area = fields.Float(string="Floor Area", track_visibility="always")
    lot_area = fields.Float(string="Lot Area", track_visibility="always")
    house_price = fields.Monetary(string="House Price", track_visibility="always")
    house_repair_price = fields.Monetary(string="House Repair Price", track_visibility="always")
    parking_price = fields.Monetary(string="Parking Price", track_visibility="always")
    lot_price = fields.Monetary(string="Lot Price", track_visibility="always")
    vat = fields.Monetary(string="Tax Amount", track_visibility="always")
    miscellaneous_charge = fields.Float(string="Miscellaneous Charge", track_visibility="always")
    condo_price = fields.Monetary(string="Condo Price", track_visibility="always")
    premium_price = fields.Monetary(string="Premium Price", track_visibility="always")

    miscellaneous_value = fields.Monetary(string="MCC2", help="Miscellaneous Absolute Value", track_visibility="always")
    miscellaneous_amount = fields.Monetary(string="Miscellaneous Amount", track_visibility="always")
    ntcp = fields.Monetary(string="NTCP", help="Total Net Contract Price", track_visibility="always")
    tcp = fields.Monetary(string="TCP", help="Total Contract Price", track_visibility="always")
    price_range_id = fields.Many2one('property.price.range', string="TCP Price Range", compute="_get_price_range",
                                     store=True)
    sale_document_requirement_ids = fields.Many2many('property.sale.required.document', 'property_sale_document_rel',
                                                     string="Document List")
    document_requirement_list_ids = fields.Many2many('property.sale.required.document', 'document_requirement_list_rel',
                                                     compute='_get_document_requirement_list',
                                                     string="Document Requirement List")
    stage_document_requirement_list_ids = fields.Many2many('property.sale.required.document',
                                                           'stage_document_requirement_list_rel',
                                                           compute='_get_stage_document_requirement_list_ids',
                                                           string="Document Requirement List")

    submitted_document_line_ids = fields.One2many('property.document.submission.line', 'property_sale_id')
    stage_document_list = fields.Html(compute="_get_stage_document_list")
    dp_percent = fields.Float(string="DP Percent")
    dp_amount = fields.Monetary(string="Down Payment Amount")
    reservation_fee = fields.Monetary(string="Reservation Fee")
    # dp_spot_cash = fields.Monetary(string="DP Spot Cash")
    # dp_due = fields.Monetary(string="DP Due", help="DP Amount less the DP Spot Cash, Reservation, and Total Discount")
    dp_monthly = fields.Monetary(string="Monthly DP")
    dp_terms = fields.Integer(string="DP in Months", help="Down Payment in number of months")
    loanable_amount = fields.Monetary(string="Loanable Amount", track_visibility="always")
    interest_rates = fields.Char(string="Interest Rates", track_visibility="always")
    la_interest = fields.Float(string="Lot Amortization Interest")
    financing_type = fields.Selection([
        ('B01', 'VLUSA Financing'),
        ('BNK', 'Bank'),
        # ('CTS', 'CTS Financing'),
        # ('D01', 'Variations Defer Financing'),
        ('DEF', 'Deferred'),
        # ('I01', 'Variations In-house Financing'),
        ('INH', 'In-House Financing'),
        ('MSI', 'Mass Housing Special In-House Financing'),
        ('OFF', 'Off-setting'),
        ('PIF', 'PIF'),
        # ('PRO', 'Provident'),
        ('RET', 'Retention'),
        ('RTB', 'Rent to Own Bank'),
        ('RTD', 'Rent to Own Deferred'),
        ('RTI', 'Rent to Own In-House Financing'),
        ('SIH', 'Special In-House Financing'),
        ('SPT', 'Spot Cash'),
        # ('SSS', 'SSS'),
        # ('STF', 'Straight Financing'),
        # ('SWP', 'Swapping')
    ], string="Financing Type", track_visibility="always")

    financing_terms = fields.Integer(string="Financing Terms", help="Lot Amortization Terms in Months",
                                     track_visibility="always")
    monthly_amortization = fields.Monetary(string="Monthly Amortization", track_visibility="always")
    first_dp_due_date = fields.Date(string="First DP Due Date", track_visibility="always")
    first_dp_due_paid = fields.Boolean(string="First DP Paid", track_visibility="always")
    broker_group = fields.Selection([
        ('Office Sales', 'Office Sales'),
        ('Digital Marketing', 'Digital Marketing'),
        ('Direct Marketing', 'Direct Marketing'),
        ('Broker', 'Broker'),
        ('Marketing Subs', 'Marketing Subs'),
        ('International Sales', 'International Sales')], string="Broker Group")

    broker_partner_id = fields.Many2one('res.partner', string="Broker", track_visibility="always", store=True,
                                        compute='_get_broker_unique_number', inverse='_inverse_customer_details')
    broker_commission_rate = fields.Float(string="Broker Commission Rate", track_visibility="always")
    broker_commission_value = fields.Float(string="Broker Commission Value", track_visibility="always")
    broker_unique_number = fields.Char(string="Broker Unique Number",
                                       help="Unique Number assigned to broker contact info.")
    realty_partner_id = fields.Many2one('res.partner', string="Realty", track_visibility="always", store=True,
                                        compute='_get_realty_unique_number', inverse='_inverse_customer_details')
    realty_commission_rate = fields.Float(string="Realty Commission Rate", track_visibility="always")
    realty_commission_value = fields.Float(string="Realty Commission Value", track_visibility="always")
    realty_unique_number = fields.Char(string="Realty Unique Number",
                                       help="Unique Number assigned to Realty contact info.")
    managing_director_partner_id = fields.Many2one('res.partner', string="Managing Director", track_visibility="always")
    managing_director_commission_rate = fields.Float(string="Managing Director Commission Rate",
                                                     track_visibility="always")
    managing_director_commission_value = fields.Float(string="Managing Director Commission Value",
                                                      track_visibility="always")
    managing_director_unique_number = fields.Char(string="Managing Director Unique Number",
                                                  help="Unique Number assigned to Managing Director contact info.")
    property_consultant_partner_id = fields.Many2one('res.partner', string="Property Consultant",
                                                     track_visibility="always")
    property_consultant_commission_rate = fields.Float(string="Property Consultant Commission Rate",
                                                       track_visibility="always")
    property_consultant_commission_value = fields.Float(string="Property Consultant Commission Value",
                                                        track_visibility="always")
    property_consultant_unique_number = fields.Char(string="Property Consultant Unique Number",
                                                    help="Unique Number assigned to Property Consultant contact info.")
    area_sales_manager_partner_id = fields.Many2one('res.partner', string="Area Sales Manager",
                                                    track_visibility="always")
    area_sales_manager_commission_rate = fields.Float(string="Area Sales Manager Commission Rate",
                                                      track_visibility="always")
    area_sales_manager_commission_value = fields.Float(string="Area Sales Manager Commission Value",
                                                       track_visibility="always")
    area_sales_manager_unique_number = fields.Char(string="Area Sales Manager Unique Number",
                                                   help="Unique Number assigned to Area Sales Manager contact info.")
    director_partner_id = fields.Many2one('res.partner', string="Director", track_visibility="always")
    director_commission_rate = fields.Float(string="Director Commission Rate", track_visibility="always")
    director_commission_value = fields.Float(string="Director Commission Value", track_visibility="always")
    director_unique_number = fields.Char(string="Director Unique Number",
                                         help="Unique Number assigned to director contact info.")
    referral_agent_partner_id = fields.Many2one('res.partner', string="Referral Agent", track_visibility="always")
    referral_agent_commission_rate = fields.Float(string="Referral Agent Commission Rate", track_visibility="always")
    referral_agent_commission_value = fields.Float(string="Referral Agent Commission Value", track_visibility="always")
    referral_agent_unique_number = fields.Char(string="Referral Agent Unique Number",
                                               help="Unique Number assigned to Referral Agent contact info.")
    sales_manager_partner_id = fields.Many2one('res.partner', string="Sales Manager", track_visibility="always")
    sales_manager_commission_rate = fields.Float(string="Sales Manager Commission Rate", track_visibility="always")
    sales_manager_commission_value = fields.Float(string="Sales Manager Commission Value", track_visibility="always")
    sales_manager_unique_number = fields.Char(string="Sales Manager",
                                              help="Unique Number assigned to Sales Manager contact info.")

    agent_position = fields.Char(string="Partner Function", track_visibility="always")
    agent_partner_id = fields.Many2one('res.partner', string="Agent",
                                       track_visibility="always", store=True,
                                       compute='_get_agent_number',
                                       inverse='_inverse_customer_details')
    agent_commission_rate = fields.Float(string="Agent Commission Rate", track_visibility="always")
    agent_commission_value = fields.Float(string="Agent Commission Value", track_visibility="always")
    agent_unique_number = fields.Char(string="Agent Unique Number",
                                      help="Unique Number assigned to Referral Agent contact info.")
    email_preferred_billing_channel = fields.Boolean(string="Email")
    sms_preferred_billing_channel = fields.Boolean(string="SMS")
    online_preferred_billing_channel = fields.Boolean(string="Online")
    hardcopy_preferred_billing_channel = fields.Boolean(string="Hard Copy")
    soa_id = fields.Many2one('property.sale.statement.of.account', string="SOA", compute="_get_soa")
    soa_number = fields.Char(string="SOA Number", compute="_get_soa")
    soa_date_generated = fields.Date(string="Date Generated", compute="_get_soa")
    soa_date = fields.Date(string="SOA Date", compute="_get_soa")
    soa_due_date = fields.Date(string="Due Date", compute="_get_soa")
    soa_current_amount = fields.Monetary(string="Current Amount Dues", compute="_get_soa")
    soa_penalty = fields.Monetary(string="Penalty", compute="_get_soa")
    soa_past_due = fields.Monetary(string="Past Dues", compute="_get_soa")
    soa_past_due_count = fields.Integer(string="Past Due Count", compute="_get_soa")
    soa_total_amount_due = fields.Monetary(string="Total Amount Due", compute="_get_soa")
    outstanding_balance = fields.Monetary(string="Outstanding Balance", compute="_get_payment_lines")
    total_principal_amount_paid = fields.Monetary(string="Total Principal Amount", compute="_get_payment_lines")
    total_interest_amount_paid = fields.Monetary(string="Total Interest Amount", compute="_get_payment_lines")
    total_penalty_paid = fields.Monetary(string="Total Penalty (Sundry)", compute="_get_payment_lines")
    grand_total_paid = fields.Monetary(string="Grand Total Paid", compute="_get_payment_lines")

    # Bank loan
    loan_application_date = fields.Date(string="Loan Application Date", track_visibility="always")
    processor = fields.Selection([('Developer Initiated', 'Developer Initiated'),
                                  ('Buyer Initiated', 'Buyer Initiated')], string="Processor",
                                 track_visibility="always")
    loan_desired_amount = fields.Monetary(string="Loan Desired Amount", track_visibility="always")
    selected_bank_application_id = fields.Many2one('property.sale.bank.loan.application',
                                                   string="Selected Bank Application", track_visibility="always")
    bank_id = fields.Many2one('res.bank', string="Bank", store=True, related="selected_bank_application_id.bank_id")
    approved_loan_amount = fields.Monetary(string="Approve Amount", store=True,
                                           related="selected_bank_application_id.approved_loan_amount")
    loan_excess_difference_amount = fields.Monetary(string="Excess/Difference", track_visibility="always")
    bank_fee = fields.Monetary(string="Bank Fee", store=True, related="selected_bank_application_id.bank_fee")
    net_proceeds = fields.Monetary(string="Net Proceeds", store=True,
                                   related="selected_bank_application_id.net_proceeds")
    approved_date = fields.Date(string="Approved Date", store=True,
                                related="selected_bank_application_id.approved_date")
    valid_until = fields.Date(string="Valid Until", store=True, related="selected_bank_application_id.valid_until")
    loan_released_date = fields.Date(strin="Loan Released Date", track_visibility="always")
    log_status = fields.Selection(
        [('signed', 'Signed'), ('notarized', 'Notarized'), ('delivered', 'Delivered to Bank')],
        string="Letter of Guarantee", track_visibility="always")
    lr_incentive = fields.Boolean(string="With LR Incentive", track_visibility="always")
    lr_incentive_amount = fields.Monetary(string="Incentive Amount", track_visibility="always")
    lr_incentive_status = fields.Selection([('endorsed', 'Endorsed'), ('released', 'Released')],
                                           string="LR Incentive Status")
    loan_application_count = fields.Integer(compute="_get_bank_loan_application_count")

    # Pagibig Loan
    credit_investigation_state = fields.Selection([
        ('not started', 'Not Started'),
        ('in progress', 'In Progress'),
        ('verified', 'Verified'),
        ('declined', 'Declined'),
    ], string="CI Status", default='not started', track_visibility="always")
    completion_date = fields.Date(string="Completion Date", track_visibility="always")
    ci_advance_date = fields.Date(string="Advance CI Date", track_visibility="always")
    ci_folder_delivery_date = fields.Date(string="folder Delivery Date", track_visibility="always")
    ci_notice_approval_date = fields.Date('Notice of Approval Date', track_visibility="always")
    ci_notice_declined_date = fields.Date(string="Notice of Decline Date", track_visibility="always")
    ci_note = fields.Text(string="CI Note", track_visibility="always")
    borrower_validation_seminar_date = fields.Date(string="BVS Date attended",
                                                   help="Borrower's Validation Seminar",
                                                   track_visibility="always")
    bvs_attendance_sheet = fields.Boolean('Attendance Sheet', track_visibility="always")
    bvs_signed = fields.Boolean(string="Signed BVS form", track_visibility="always")
    members_saving_validation_system = fields.Selection([
        ('pending', 'Pending'),
        ('with msvs finding', 'With MSVS Finding'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ], string="MSVS Status", default='pending', track_visibility="always",
        help="Members Savings Validation System")
    msvs_date_approved = fields.Date(string="MSVS Date Approved", track_visibility="always")
    epeb_title_number = fields.Char(string="Title Number", help="Electronic Processing Entry Book",
                                    track_visibility="always")
    epeb_endorsement_date = fields.Date(string="Endorsement Date", help="Electronic Processing Entry Book",
                                        track_visibility="always")
    epeb_title_released_date = fields.Date(string="Title Released Date", help="Electronic Processing Entry Book",
                                           track_visibility="always")
    pif_loan_approved_amount = fields.Monetary(string="PIF Approved Amount", track_visibility="always")
    pif_to_date = fields.Date(string="PIF Take Out Date", track_visibility="always")
    pif_deduction = fields.Monetary(string="PIF Deductions", track_visibility="always")
    pif_deduction_notes = fields.Text(string='PIF Deductions Notes', track_visibility="always")
    pif_net_proceeds = fields.Monetary(string="PIF Net Proceeds", track_visibility="always")
    pif_loan_status = fields.Selection([
        ('ongoing', 'Ongoing'),
        ('taken_out', 'Taken Out'),
        ('declined', 'Declined'),
        ('shifted', 'Shifted')
    ], string="PIF Loan Status", default="ongoing", track_visibility="always")
    pif_declined_date = fields.Date(string="PIF Declined Date", track_visibility="always")
    pif_declined_notes = fields.Text(string="PIF Declined Notes", track_visibility="always")
    pif_inspection_ids = fields.One2many('property.inspection', 'property_sale_id')
    # Inhouse Financing
    if_type = fields.Selection([
        ('regular in-house', 'Regular In-house'),
        ('shifted', 'Shifted'),
        ('buy back', 'Buy Back')
    ], string="IF Type", track_visibility="always")
    if_cwt_paid = fields.Boolean(string="CWT Paid?", track_visibility="always")
    if_cwt_paid_date = fields.Date(string="CWT Paid Date", track_visibility="always")
    ticket_count = fields.Integer("Tickets", compute='_compute_ticket_count')
    doc_submission_due_date = fields.Date(string="Document Submission Due Date", store=True,
                                          compute="_get_doc_submission_due_date")
    doc_submission_due_date_reminder = fields.Date(string="Document Submission Due Date Reminder", store=True,
                                                   compute="_get_doc_submission_due_date")
    admin_qualified = fields.Boolean(string="Is Admin Qualified", track_visibility="always")
    other_note = fields.Text(string="Other Notes")

    @api.onchange('sales_manager_partner_id', 'referral_agent_partner_id', 'director_partner_id',
                  'area_sales_manager_partner_id',
                  'property_consultant_partner_id', 'managing_director_partner_id', 'realty_partner_id',
                  'broker_partner_id', 'agent_partner_id')
    def onchange_sale_accounts(self):
        if self.sales_manager_partner_id:
            self.sales_manager_unique_number = self.sales_manager_partner_id.sales_account_number
        if self.referral_agent_partner_id:
            self.referral_agent_unique_number = self.referral_agent_partner_id.sales_account_number
        if self.director_partner_id:
            self.director_unique_number = self.director_partner_id.sales_account_number
        if self.area_sales_manager_partner_id:
            self.area_sales_manager_unique_number = self.area_sales_manager_partner_id.sales_account_number
        if self.property_consultant_partner_id:
            self.property_consultant_unique_number = self.property_consultant_partner_id.sales_account_number
        if self.managing_director_partner_id:
            self.managing_director_unique_number = self.managing_director_partner_id.sales_account_number
        if self.realty_partner_id:
            self.realty_unique_number = self.realty_partner_id.sales_account_number
        if self.broker_partner_id:
            self.broker_unique_number = self.broker_partner_id.sales_account_number
        if self.agent_partner_id:
            self.agent_unique_number = self.agent_partner_id.sales_account_number

    def _inverse_customer_details(self):
        for r in self:
            continue

    @api.depends('agent_unique_number')
    def _get_agent_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.agent_partner_id = False
            if r.sales_manager_unique_number:
                partner = contact.search([('sales_account_number', '=', r.agent_unique_number)], limit=1)
                r.agent_partner_id = partner[:1] and partner.id or False

    @api.depends('sales_manager_unique_number')
    def _get_sales_manager_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.sales_manager_partner_id = False
            if r.sales_manager_unique_number:
                partner = contact.search([('sales_account_number', '=', r.sales_manager_unique_number)], limit=1)
                r.sales_manager_partner_id = partner[:1] and partner.id or False

    @api.depends('referral_agent_unique_number')
    def _get_referral_agent_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.referral_agent_partner_id = False
            if r.referral_agent_unique_number:
                partner = contact.search([('sales_account_number', '=', r.referral_agent_unique_number)], limit=1)
                r.referral_agent_partner_id = partner[:1] and partner.id or False

    @api.depends('director_unique_number')
    def _get_director_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.director_partner_id = False
            if r.director_unique_number:
                partner = contact.search([('sales_account_number', '=', r.director_unique_number)], limit=1)
                r.director_partner_id = partner[:1] and partner.id or False

    @api.depends('area_sales_manager_unique_number')
    def _get_area_sales_manager_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.area_sales_manager_partner_id = False
            if r.area_sales_manager_unique_number:
                partner = contact.search([('sales_account_number', '=', r.area_sales_manager_unique_number)], limit=1)
                r.area_sales_manager_partner_id = partner[:1] and partner.id or False

    @api.depends('property_consultant_unique_number')
    def _get_property_consultant_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.property_consultant_partner_id = False
            if r.property_consultant_unique_number:
                partner = contact.search([('sales_account_number', '=', r.property_consultant_unique_number)], limit=1)
                r.property_consultant_partner_id = partner[:1] and partner.id or False

    @api.depends('managing_director_unique_number')
    def _get_managing_director_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.managing_director_partner_id = False
            if r.managing_director_unique_number:
                partner = contact.search([('sales_account_number', '=', r.managing_director_unique_number)], limit=1)
                r.managing_director_partner_id = partner[:1] and partner.id or False

    @api.depends('realty_unique_number')
    def _get_realty_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.realty_partner_id = False
            if r.realty_unique_number:
                partner = contact.search([('sales_account_number', '=', r.realty_unique_number)], limit=1)
                r.realty_partner_id = partner[:1] and partner.id or False

    @api.depends('broker_unique_number')
    def _get_broker_unique_number(self):
        contact = self.env['res.partner']
        for r in self:
            r.broker_partner_id = False
            if r.broker_unique_number:
                partner = contact.search([('sales_account_number', '=', r.broker_unique_number)], limit=1)
                r.broker_partner_id = partner[:1] and partner.id or False

    @api.depends('so_date', 'stage_id', 'stage_id.document_submission_days', 'stage_id.document_submission_reminder')
    def _get_doc_submission_due_date(self):
        for r in self:
            if r.so_date and r.stage_id and r.stage_id.document_submission_days > 0:
                r.doc_submission_due_date = r.so_date + timedelta(days=r.stage_id.document_submission_days)
                r.doc_submission_due_date_reminder = r.so_date + timedelta(days=r.stage_id.document_submission_reminder)

    def cron_document_due_reminder(self):
        stage_data = self.env['property.sale.status'].sudo().search([
            ('active', '=', True),
            ('canceled', '=', False)])
        for stage in stage_data:
            if stage.document_submission_days > 0:
                for r in self.search([('stage_id', '=', stage.id)]):
                    if r.partner_id and r.doc_submission_due_date:
                        send_reminder = False
                        for doc in r.stage_document_requirement_list_ids:
                            if doc.submitted_by_buyer:
                                send_reminder = True
                                break
                        if send_reminder:
                            email_temp = self.env.ref(
                                'property_admin_monitoring.email_template_document_submission_due_date_reminder')
                            r.message_post_with_template(email_temp.id)

    def _compute_ticket_count(self):
        for r in self:
            r.ticket_count = self.env['helpdesk.ticket'].sudo().search_count([('so_number', '=', r.so_number)])

    def action_open_helpdesk_ticket(self):
        action = self.env.ref('helpdesk.helpdesk_ticket_action_main_tree').read()[0]
        action['context'] = {}
        action['domain'] = [('so_number', '=', self.so_number)]
        return action

    def _get_ticket_details(self, sale_id):
        sale_doc = self.sudo().browse(sale_id)
        ticket = self.env['helpdesk.ticket'].sudo().search([('so_number', '=', sale_doc.so_number)])
        ticket_list = list()
        for r in ticket:
            data = {
                'id': r.id,
                'assigned_team': r.team_id and r.team_id.name or None,
                'assigned_person': r.user_id and r.user_id.name or None,
                'ticket_type': r.ticket_type_id and r.ticket_type_id.name or None,
                'ticket_status': r.stage_id.name,
                'description': r.description,
                'create_date': r.create_date,
                'closed_date': r.close_date,
            }
            ticket_list.append(data)
        return ticket_list

    def _get_complete_address(self, project_location):
        location = ""
        location += f"{project_location.street} "
        if project_location.street2:
            location += f"{project_location.street2}"
        if project_location.barangay_id:
            if location != "":
                location += ", "
            location += f"{project_location.barangay_id.name}"
        if project_location.city_id:
            if location != "":
                location += ", "
            location += f"{project_location.city_id.name}"
        if project_location.province_id:
            if location != "":
                location += ", "
            location += f"{project_location.province_id.name}"
        if project_location.state_id:
            if location != "":
                location += ", "
            location += f"{project_location.state_id.name}"
        if project_location.zip:
            if location != "":
                location += ", "
            location += f"{project_location.zip}"
        if project_location.country_id:
            if location != "":
                location += ", "
            location += f"{project_location.country_id.name}"
        return location

    def _get_customer_properties(self, partner_id):
        sales_property = self.env['property.admin.sale'].sudo().search([('partner_id', '=', partner_id)])
        return sales_property

    def _get_customer_properties_with_details(self, partner_id):
        sales_property = self.env['property.admin.sale'].sudo().search([('partner_id', '=', partner_id)])
        data = list()
        for r in sales_property:
            data.append({
                'company_id': r.company_id.id,
                'company_name': r.company_id.name,
                'company_code': r.company_id.code,
                'be_code': r.be_code,
                'brand': r.brand,
                'project_id': r.subdivision_phase_id.id,
                'project_name': r.subdivision_phase_id.name,
                'property_id': r.property_id.id,
                'property_name': r.property_id.name,
                'house_model': r.house_model_id.name,
                'block_lot': r.block_lot,
                'address': r._get_complete_address(r.subdivision_phase_id),
                'so_number': r.so_number,
                'sale_id': r.id
            })
        return data

    def _get_property_info(self, sale_id):
        r = self.sudo().browse(sale_id)
        total_dp_amount_paid = r.total_principal_amount_paid
        total_loan_amount_paid = 0
        total_loan_amount_paid_percent = 0
        if total_dp_amount_paid > r.dp_amount:
            total_dp_amount_paid_percent = 100
            total_loan_amount_paid = total_dp_amount_paid - r.dp_amount
            total_dp_amount_paid = r.dp_amount
            total_loan_amount_paid_percent = (total_loan_amount_paid / r.loanable_amount if r.loanable_amount else 0) * 100
        else:
            total_dp_amount_paid_percent = (total_dp_amount_paid / r.dp_amount if r.dp_amount else 0) * 100
        data = {}
        dp_amount_readable = self.human_readable_number_format(r.dp_amount)
        loanable_amount_readable = self.human_readable_number_format(r.loanable_amount)
        data.update({
            'id': r.id,
            'project_name': r.subdivision_phase_id.name,
            'property_name': r.property_id.name,
            'house_model': r.house_model_id.name,
            'block_lot': r.block_lot,
            'floor_area': r.floor_area,
            'lot_area': r.lot_area,
            'address': r._get_complete_address(r.subdivision_phase_id),
            'tcp': r.tcp,
            'downpayment_amount': r.dp_amount,
            'downpayment_percent': r.dp_percent,
            'total_dp_amount_paid': total_dp_amount_paid,
            'total_dp_amount_paid_percent': total_dp_amount_paid_percent,
            'loanable_amount': r.loanable_amount,
            'total_loan_amount_paid': total_loan_amount_paid,
            'total_loan_amount_paid_percent': total_loan_amount_paid_percent,
            'total_principal_amount_paid': r.total_principal_amount_paid,
            'total_interest_amount_paid': r.total_interest_amount_paid,
            'total_penalty_paid': r.total_penalty_paid,
            'grand_total_paid': r.grand_total_paid,
            'outstanding_balance': r.outstanding_balance,
            'downpayment_amount_readable_format': dp_amount_readable,
            'loanable_amount_readable_format': loanable_amount_readable,
        })
        soa = self.get_latest_soa(r.so_number)
        if soa:
            data['latest_soa'] = {
                'id': soa.id,
                'soa_number': soa.soa_number,
                'soa_date_generated': soa.date_generated,
                'soa_date': soa.soa_date,
                'soa_due_date': soa.soa_due_date,
                'soa_current_amount': soa.current_amount,
                'soa_penalty': soa.penalty,
                'soa_total_amount_due': soa.total_amount_due,
                'soa_past_due': soa.past_due
            }
            soa_line = list()
            for line in soa.past_due_line_ids:
                soa_line.append({
                    'id': line.id,
                    'bill_number': line.bill_number,
                    'bill_date': line.bill_date,
                    'billing_amount': line.billing_amount,
                    'penalty': line.penalty,
                    'amount_due': line.amount_due
                })
            if soa_line:
                data['latest_soa']['past_due_breakdown'] = soa_line
        return data

    def _get_soa_list(self, sale_id):
        sale_doc = self.sudo().browse(sale_id)
        soa_list = self.env['property.sale.statement.of.account'].sudo().search([
            ('so_number', '=', sale_doc.so_number)
        ])
        soa_docs = list()
        for soa in soa_list:
            data = {
                'id': soa.id,
                'soa_number': soa.soa_number,
                'soa_date_generated': soa.date_generated,
                'soa_date': soa.soa_date,
                'soa_due_date': soa.soa_due_date,
                'soa_current_amount': soa.current_amount,
                'soa_penalty': soa.penalty,
                'soa_past_due': soa.past_due,
                'soa_total_amount_due': soa.total_amount_due,
            }
            soa_line = list()
            for line in soa.past_due_line_ids:
                soa_line.append({
                    'id': line.id,
                    'bill_number': line.bill_number,
                    'bill_date': line.bill_date,
                    'billing_amount': line.billing_amount,
                    'penalty': line.penalty,
                    'amount_due': line.amount_due
                })
            if soa_line:
                data['past_due_breakdown'] = soa_line
            soa_docs.append(data)
        return soa_docs

    def _get_document_requirement_list_portal(self, sale_id):
        sale_doc = self.sudo().browse(sale_id)
        documents = list()
        for r in sale_doc.document_requirement_list_ids:
            data = {
                'id': r.id,
                'document_name': r.name,
                'document_description': r.description,
                'document_note': r.note,
                'optional_requirement': r.optional_requirement,
                'document_sequence': r.sequence,
                'document_preview': r.preview_file,
                'preview_file_name': r.preview_file_name,
            }
            submitted_doc = self.env['property.document.submission.line'].sudo().search([
                                                    ('property_sale_id', '=', sale_id),
                                                    ('document_id', '=', r.id)
                                                ], limit=1)
            if submitted_doc[:1]:
                data.update({
                    'document_validated_date': submitted_doc.validation_date,
                    'document_expiry_date': submitted_doc.expiry_date,
                    'document_validation_note': submitted_doc.note
                })
            query = """ SELECT * FROM property_sale_document_rel
                        WHERE property_admin_sale_id = %s
                        AND property_sale_required_document_id = %s"""
            self.env.cr.execute(query, (sale_id, r.id,))
            document_checklist = self.env.cr.fetchone() or []
            if document_checklist:
                data.update({'checked': True})
            else:
                data.update({'checked': False})
            documents.append(data)
        return documents

    def _get_document_downloadable_list_portal(self):
        downloadables = self.env['property.sale.downloadable.document'].sudo().search([('active', '=', True)])
        documents = list()
        for r in downloadables:
            documents.append({
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'sequence': r.sequence,
                'attachment_file': r.attachment_file
            })
        return documents

    def _get_bank_loan_application_count(self):
        loan_application = self.env['property.sale.bank.loan.application']
        for r in self:
            r.loan_application_count = loan_application.search_count([('property_sale_id', '=', r.id)])

    @api.onchange('selected_bank_application_id', 'loan_desired_amount')
    def _onchange_bank_selected(self):
        if self.selected_bank_application_id:
            self.loan_excess_difference_amount = abs(
                self.selected_bank_application_id.approved_loan_amount - self.loan_desired_amount)

    def get_latest_soa(self, so_number):
        soa = self.env['property.sale.statement.of.account'].sudo().search([('so_number', '=', so_number)],
                                                                           order='soa_date desc')
        if soa[:1]:
            return soa[0]
        else:
            return False

    def _get_soa(self):
        for i in self:
            soa = self.get_latest_soa(i.so_number)
            i.soa_id = soa
            i.soa_number = soa and soa.soa_number or False
            i.soa_date_generated = soa and soa.date_generated
            i.soa_date = soa and soa.soa_date
            i.soa_due_date = soa and soa.soa_due_date
            i.soa_current_amount = soa and soa.current_amount
            i.soa_penalty = soa and soa.penalty
            i.soa_past_due = soa and soa.past_due
            i.soa_past_due_count = soa and soa.past_due_count
            i.soa_total_amount_due = soa and soa.total_amount_due

    def _get_stage_document_list(self):
        for r in self:
            document = ''
            if r.stage_id:
                count = 1
                for gd in r.stage_id.required_sale_document_requirement_ids:
                    if not gd.employment_status_id:
                        if gd.optional_requirement:
                            document += f"<ul>{count}. {gd.name} - (Optional))</ul>"
                        else:
                            document += f"<ul>{count}. {gd.name}</ul>"
                    elif r.employment_status_id and gd.employment_status_id.id == r.employment_status_id.id:
                        if gd.optional_requirement:
                            document += f"<ul>{count}. {gd.name} - (Optional))</ul>"
                        else:
                            document += f"<ul>{count}. {gd.name}</ul>"
                    count += 1
                for psd in r.stage_id.project_specific_document_ids:
                    if psd.be_code == r.be_code:
                        for psd_document in psd.required_sale_document_requirement_ids:
                            if not psd_document.employment_status_id:
                                if psd_document.optional_requirement:
                                    document += f"<ul>{count}. {psd_document.name} - (Optional))</ul>"
                                else:
                                    document += f"<ul>{count}. {psd_document.name}</ul>"
                            elif r.employment_status_id and psd_document.employment_status_id.id == r.employment_status_id.id:
                                if psd_document.optional_requirement:
                                    document += f"<ul>{count}. {psd_document.name} - (Optional))</ul>"
                                else:
                                    document += f"<ul>{count}. {psd_document.name}</ul>"
                    count += 1
            r.stage_document_list = document

    @api.depends('be_code', 'partner_id', 'employment_status_id', 'stage_id.project_specific_document_ids',
                 'stage_id.required_sale_document_requirement_ids',
                 'stage_id.project_specific_document_ids.required_sale_document_requirement_ids')
    def _get_document_requirement_list(self):
        for r in self:
            stages = self.env['property.sale.status'].search([('active', '=', True), ('canceled', '=', False)])
            documents = list()
            for i in stages:
                for gd in i.required_sale_document_requirement_ids:
                    if not gd.employment_status_id:
                        documents.append(gd.id)
                    elif r.employment_status_id and gd.employment_status_id.id == r.employment_status_id.id:
                        documents.append(gd.id)
                for psd in i.project_specific_document_ids:
                    if psd.be_code == r.be_code:
                        for psd_document in psd.required_sale_document_requirement_ids:
                            if not psd_document.employment_status_id:
                                documents.append(psd_document.id)
                            elif r.employment_status_id and psd_document.employment_status_id.id == r.employment_status_id.id:
                                documents.append(psd_document.id)
            r.document_requirement_list_ids = documents

    @api.depends('stage_id', 'sale_document_requirement_ids')
    def _get_stage_document_requirement_list_ids(self):
        for r in self:
            validated_doc = r.sale_document_requirement_ids.ids
            document = list()
            if r.stage_id:
                for gd in r.stage_id.required_sale_document_requirement_ids:
                    if not gd.employment_status_id:
                        if not gd.id in validated_doc:
                            document.append(gd.id)
                    elif r.employment_status_id and gd.employment_status_id.id == r.employment_status_id.id:
                        if not gd.id in validated_doc:
                            document.append(gd.id)
                for psd in r.stage_id.project_specific_document_ids:
                    if psd.be_code == r.be_code:
                        for psd_document in psd.required_sale_document_requirement_ids:
                            if not psd_document.employment_status_id:
                                if not psd_document.id in validated_doc:
                                    document.append(psd_document.id)
                            elif r.employment_status_id and psd_document.employment_status_id.id == r.employment_status_id.id:
                                if not psd_document.id in validated_doc:
                                    document.append(psd_document.id)
            r.stage_document_requirement_list_ids = document

    # @api.constrains('stage_id', 'sale_document_requirement_ids')
    def _validate_document_requirement(self):
        msg = ""
        for data in self:
            required_doc = ""
            # _logger.info(f"\n\nStage: {data.stage_id.predecessor_stage_id.name}\n\n")
            if not data.stage_id.canceled and data.stage_id.predecessor_stage_id:
                predecessor = data.stage_id.predecessor_stage_id
                while predecessor:
                    for req in predecessor.required_sale_document_requirement_ids:
                        if not req.optional_requirement:
                            if not req.employment_status_id:
                                if req.id not in data.sale_document_requirement_ids.ids:
                                    required_doc += f"\t{req.name}\n"
                            elif data.employment_status_id and data.employment_status_id.id == req.employment_status_id.id:
                                if req.id not in data.sale_document_requirement_ids.ids:
                                    required_doc += f"\t{req.name}\n"
                    for psd in predecessor.project_specific_document_ids:
                        if psd.be_code == data.be_code:
                            for psd_document in psd.required_sale_document_requirement_ids:
                                if not psd_document.optional_requirement:
                                    if not psd_document.employment_status_id:
                                        if psd_document.id not in data.sale_document_requirement_ids.ids:
                                            required_doc += f"\t{psd_document.name}\n"
                                    elif data.employment_status_id and data.employment_status_id.id == psd_document.employment_status_id.id:
                                        if psd_document.id not in data.sale_document_requirement_ids.ids:
                                            required_doc += f"\t{psd_document.name}\n"
                    predecessor = predecessor.predecessor_stage_id
            if required_doc != "":
                msg += f"\nRS: {data.name}\n{required_doc}"
        if msg != "":
            raise ValidationError(_(f"The following documents are required:{msg}"))

    def _expand_stages(self, states, domain, order):
        stage_ids = self.env['property.sale.status'].search([])
        return stage_ids

    def _expand_sub_stages(self, states, domain, order):
        stage_ids = self.env['property.sale.sub.status'].search([])
        return stage_ids

    @api.depends('tcp')
    def _get_price_range(self):
        for r in self:
            if r.tcp > 0:
                price_range = self.env['property.price.range'].search(
                    [('range_from', '<=', r.tcp), ('range_to', '>=', r.tcp)], limit=1)
                r.price_range_id = price_range[:1] and price_range.id or False

    def _inverse_get_contract_price(self):
        for i in self:
            continue

    # @api.depends('property_id')
    # def _get_contract_price(self):
    #     for r in self:
    #         data = r.property_id
    #         r.lot_area = data.lot_area
    #         r.lot_area_price = data.lot_area_price
    #         r.lot_price = data.lot_price
    #         r.house_price = data.house_price
    #         r.house_repair_price = data.house_repair_price
    #         r.parking_price = data.parking_price
    #         r.floor_area = data.floor_area
    #         r.floor_area_price = data.floor_area_price
    #         r.miscellaneous_charge = data.miscellaneous_charge
    #         r.miscellaneous_value = data.miscellaneous_value
    #         r.miscellaneous_amount = data.miscellaneous_amount
    #         r.vat = data.vat
    #         r.ntcp = data.ntcp
    #         r.tcp = data.tcp

    def cancel_sale_account(self):
        cancel_stage = self.env['property.sale.status'].search([('canceled', '=', True)], limit=1)
        for r in self:
            r.write({
                'stage_id': cancel_stage.id,
                'cancellation_date': date.today(),
                'before_cancelled_stage_id': self.stage_id.id})
        return True

    def cron_compute_property_sale_status_aging(self):
        rec = self.sudo().search([])
        for r in rec:
            data = {}
            if r.stage_id.with_successor and r.moved_stage_datetime:
                data['stage_age'] = (datetime.now() - r.moved_stage_datetime).days
            if r.moved_sub_stage_datetime and r.sub_stage_id.with_successor:
                data['sub_stage_age'] = (datetime.now() - r.moved_sub_stage_datetime).days
            if data:
                r.sudo().write(data)

    def log_submitted_and_removed_docs(self, vals):
        current_ducument = self.sale_document_requirement_ids.ids
        added_document = list()
        removed_document = list()
        for d in vals.get('sale_document_requirement_ids')[0][2]:
            if not d in current_ducument:
                added_document.append(d)
        for d in current_ducument:
            if not d in vals.get('sale_document_requirement_ids')[0][2]:
                removed_document.append(d)
        body = ''
        if added_document:
            added_document_line = list()
            for r in added_document:
                added_document_line.append([0, 0, {
                    'document_id': r,
                    'validation_date': fields.Date.today()
                }])
            body += '<p> <strong><em>The following submitted document/s has been validated: </em></strong></p>'
            count = 0
            for r in self.env['property.sale.required.document'].browse(added_document):
                count += 1
                body += f"<ul>{count}. {r.name}</ul>"
            body += '<br/>'
        if removed_document:
            submitted_doc_line = self.env['property.document.submission.line']
            body += '<p><em>The following submitted document/s has been removed: </em></p>'
            count = 0
            for r in self.env['property.sale.required.document'].browse(removed_document):
                count += 1
                body += f"<ul>{count}. {r.name}</ul>"
                sdl = submitted_doc_line.search([('document_id', '=', r.id), ('property_sale_id', '=', self.id)],
                                                limit=1)
                if sdl:
                    sdl.unlink()
            body += '<br/>'
        self.message_post(body=body, subject="Document Validation Status")

    def trigger_tag_admin_qualified(self, so_number):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn = http.client.HTTPSConnection(api_key.api_url)
        payload = '[{\"VBELN\": \"%s\"}]' % (so_number)
        conn.request("POST", "/VistaAdminAPI/rest/DocsOdooMaintenance/CreateDocs", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        _logger.info(f"\n\n\nTrigger admin qualified: {str(json_data)}\n\n\n")
        return True

    # MANDT = 113 & SWENR = 5060007 & VBELN = 2100006013 & REFNO = 011 - 0006

    def check_data(self, vals):
        if vals.get('stage_id'):
            vals['stage_age'] = 0
            sub_stage = self.env['property.sale.sub.status'].search(
                [('active', '=', True), ('sub_parent_id', '=', vals.get('stage_id'))], order='sequence asc')
            vals['sub_stage_id'] = sub_stage[:1] and sub_stage[0].id or False
            property_rec = self.env['property.detail'].browse(vals.get('property_id') or self.property_id.id)
            assigned_person = self.env['property.status.assigned.person'].search(
                [('state_id', '=', vals.get('stage_id')), ('subdivision_phase_id.be_code', 'in', [property_rec.be_code])], limit=1)
            if assigned_person[:1]:
                vals[
                    'account_officer_user_id'] = assigned_person.account_officer_user_id and assigned_person.account_officer_user_id.id or (
                        self.account_officer_user_id and self.account_officer_user_id.id or False)
                vals[
                    'collection_officer_user_id'] = assigned_person.collection_officer_user_id and assigned_person.collection_officer_user_id.id or (
                        self.collection_officer_user_id and self.collection_officer_user_id.id or False)
                vals['moved_stage_datetime'] = datetime.now()
            if self.moved_stage_datetime:
                stutus_log_data = {
                    'status': self.env['property.sale.status'].browse(vals.get('stage_id')).name,
                    'status_from': self.stage_id.name,
                    'status_type': 'Status',
                    'account_officer_user_id': self.account_officer_user_id and self.account_officer_user_id.id or False,
                    'collection_officer_user_id': self.collection_officer_user_id and self.collection_officer_user_id.id or False,
                    'date_from': self.moved_stage_datetime,
                    'date_to': datetime.now(),
                    'total_days': (datetime.now() - self.moved_stage_datetime).days,
                    'user_id': self._uid
                }
                vals['status_log_ids'] = [(0, 0, stutus_log_data)]
        if 'sub_stage_id' in vals and vals.get('sub_stage_id'):
            vals['moved_sub_stage_datetime'] = datetime.now()
            vals['sub_stage_age'] = 0
            if self.moved_sub_stage_datetime and self.sub_stage_id:
                sub_stage = self.env['property.sale.sub.status'].browse(vals.get('sub_stage_id'))
                if sub_stage.trigger_admin_qualified:
                    self.trigger_tag_admin_qualified(vals.get('so_number') or self.so_number)
                stutus_log_data = {
                    'status': sub_stage.name,
                    'status_from': self.sub_stage_id.name,
                    'status_type': 'Sub-status',
                    'account_officer_user_id': self.account_officer_user_id and self.account_officer_user_id.id or False,
                    'collection_officer_user_id': self.collection_officer_user_id and self.collection_officer_user_id.id or False,
                    'date_from': self.moved_sub_stage_datetime,
                    'date_to': datetime.now(),
                    'total_days': (datetime.now() - self.moved_sub_stage_datetime).days,
                    'user_id': self._uid
                }
                if 'status_log_ids' in vals and vals.get('status_log_ids'):
                    vals['status_log_ids'] = vals.get('status_log_ids') + [(0, 0, stutus_log_data)]
                else:
                    vals['status_log_ids'] = [(0, 0, stutus_log_data)]
        elif 'sub_stage_id' in vals:
            vals['sub_stage_age'] = 0
            vals['moved_sub_stage_datetime'] = False
        if vals.get('account_officer_user_id'):
            vals['ao_assigned_date'] = date.today()
        if vals.get('collection_officer_user_id'):
            vals['co_assigned_date'] = date.today()
        if vals.get('account_officer_user_id') or vals.get('collection_officer_user_id'):
            data = {
                'account_officer_user_id': 'account_officer_user_id' in vals and vals.get(
                    'account_officer_user_id') or (
                                                   self.account_officer_user_id and self.account_officer_user_id.id or False),
                'collection_officer_user_id': 'collection_officer_user_id' in vals and vals.get(
                    'collection_officer_user_id') or (
                                                      self.collection_officer_user_id and self.collection_officer_user_id.id or False),
                'stage_id': vals.get('stage_id') or self.stage_id.id,
                'sub_stage_id': vals.get('sub_stage_id') or self.sub_stage_id and self.sub_stage_id.id or False,
                'user_id': self._uid,
            }
            vals['assignment_log_ids'] = [(0, 0, data)]
        return vals

    def write(self, vals):
        vals = self.check_data(vals)
        if 'sale_document_requirement_ids' in vals and vals.get('sale_document_requirement_ids'):
            self.log_submitted_and_removed_docs(vals)
        return super(PropertyAdminSale, self).write(vals)

    def _validate_stage_document_requirement(self, stage):
        msg = ""
        for data in self:
            required_doc = ""
            if not stage.canceled and stage.predecessor_stage_id:
                predecessor = stage.predecessor_stage_id
                # while predecessor:
                for req in predecessor.required_sale_document_requirement_ids:
                    if not req.optional_requirement:
                        if not req.employment_status_id:
                            if req.id not in data.sale_document_requirement_ids.ids:
                                required_doc += f"\t{req.name}\n"
                        elif data.employment_status_id and data.employment_status_id.id == req.employment_status_id.id:
                            if req.id not in data.sale_document_requirement_ids.ids:
                                required_doc += f"\t{req.name}\n"
                for psd in predecessor.project_specific_document_ids:
                    if psd.be_code == data.be_code:
                        for psd_document in psd.required_sale_document_requirement_ids:
                            if not psd_document.optional_requirement:
                                if not psd_document.employment_status_id:
                                    if psd_document.id not in data.sale_document_requirement_ids.ids:
                                        required_doc += f"\t{psd_document.name}\n"
                                elif data.employment_status_id and data.employment_status_id.id == psd_document.employment_status_id.id:
                                    if psd_document.id not in data.sale_document_requirement_ids.ids:
                                        required_doc += f"\t{psd_document.name}\n"

                    #Just activate this if need to retroactively need to check document requirement.
                    #predecessor = predecessor.predecessor_stage_id
            if required_doc != "":
                msg += f"\nRS: {data.name}\n{required_doc}"
        if msg != "":
            raise ValidationError(_(f"The following documents are required:{msg}"))

    def move_to_next_stage(self):
        # _logger.info(f"\n\n{self.so_number}- {self.stage_id.successor_stage_id.name}\n\n\n")
        if not self.stage_id.with_successor:
            raise ValidationError(_(f"There is no stage defined after: {self.stage_id.name}"))
        if self.stage_id.with_successor:
            self._validate_stage_document_requirement(self.stage_id.successor_stage_id)
        if self.stage_id.successor_stage_id.name == 'Uncontracted':
            if self.sub_stage_id and not self.sub_stage_id.trigger_admin_qualified:
                raise ValidationError(_("In order to move the next stage, the account must be tagged first as Admin Qualified."))
        if self.stage_id.successor_stage_id.name == 'Contracted':
            if self.db_for_contracted_sale_tracker:
                self.check_for_contracted_sale_request_status()
            else:
                total_paid = self.tcp > 0 and self.total_principal_amount_paid > 0 and (self.total_principal_amount_paid / self.tcp) * 100 or 0
                crecom = self.env['property.sale.credit.committee.approval'].search([('property_sale_id', '=', self.id)])
                crecom_approved = False
                if crecom[:1]:
                    if crecom.state == 'approved':
                        crecom_approved = True
                if not crecom_approved:
                    raise ValidationError(_("Credit Committee must be fully accomplished First in order to convert to CS Status"))
                if total_paid < 10 or total_paid < self.dp_amount:
                    raise ValidationError(_("Must meet the following Criteria in order to convert to CS Status\n\t(1) Payment = 10% of TCP or Full DP whichever comes first \n\t(2) Customer Documents = 100% complete (for customer document source)"))
                self.set_ready_for_contracted_sale()
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'Congratulation! '
                                   f'{self.so_number} is now being processed in the SAP to convert to Contracted Sales Stage',
                        'type': 'rainbow_man',
                    }
                }
        else:
            if self.stage_id.successor_stage_id.name == 'Loan Released' and self.financing_type in ['INH', 'SPT', 'RTB',
                                                                                                    'RTI', 'DEF',
                                                                                                    'OFF']:
                self.write({'stage_id': self.stage_id.successor_stage_id.successor_stage_id.id})
            else:
                self.write({'stage_id': self.stage_id.successor_stage_id.id})

    def set_release_advance_commission(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn = http.client.HTTPSConnection(api_key.api_url)
        payload = '[{\"MANDT\": \"%s\", \"VBELN\": \"%s\", \"BUKRS\": \"%s\"}]' % (
            self.company_id.sap_client_id, self.so_number, self.company_id.code)
        conn.request("POST", "/VistaAdminAPI/rest/SOAdvCom/CreateSOAdvCom", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        self.write({
            'db_release_commission_tracker': json_data,
            'request_released_commission': True
        })
        return True

    def cron_check_release_advance_commission(self):
        data = self.sudo().search([('db_release_commission_tracker', '>', 0), ('released_commission', '=', False)])
        for r in data:
            r.check_release_advance_commission()

    def check_release_advance_commission(self):
        if self.db_release_commission_tracker != 0:
            api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
            conn = http.client.HTTPSConnection(api_key.api_url)
            headers = {'X-AppKey': api_key.api_app_key,
                       'X-AppId': api_key.api_app_id,
                       'Content-Type': api_key.api_content_type}
            conn.request("GET", f"/VistaAdminAPI/rest/SOAdvCom/GetSOAdvCom?id={self.db_release_commission_tracker}", [],
                         headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            if json_data and json_data[0].get("STATUS") in ['1', '2']:
                vals = {
                    "db_release_commission_log": json_data[0].get("MESSAGELOG")
                }
                if json_data[0].get("STATUS") == '2':
                    vals['db_release_commission_tracker'] = 0
                    vals['request_released_commission'] = False
                    msg = f"<p>Hi {self.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for release advance commission for the said SO was unable to process in our SAP system." \
                          f"due to the ff. reason/s: <em>{json_data[0].get('MESSAGELOG')}</em></p>"
                else:
                    vals['released_commission'] = True
                    msg = f"<p>Hi {self.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for release advance commission for the said SO is already being processed in our SAP system.</p>"
                self.sudo().write(vals)
                post_vars = {'partner_ids': [self.account_officer_user_id.partner_id.id]}
                subject = f"{self.subdivision_phase_id.brand} - Releasing of Advance Commission {self.so_number}"
                self.message_post(body=msg, subject=subject, **post_vars)
        return True

    def set_ready_for_contracted_sale(self):
        stage = self.env['property.sale.status'].search(
            [('active', '=', True), ('name', '=', 'Contracted')], limit=1)
        self._validate_stage_document_requirement(stage)
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn = http.client.HTTPSConnection(api_key.api_url)
        payload = '[{\"MANDT\": \"%s\", \"VBELN\": \"%s\", \"BUKRS\": \"%s\"}]' % (
            self.company_id.sap_client_id, self.so_number, self.company_id.code)
        conn.request("POST", "/VistaAdminAPI/rest/SOContract/CreateSOContract", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        # _logger.info(f"\n\n\nPayload: {payload}\n API Return: {json_data}\n\n")
        self.write({
            'for_contracted_sale_user_id': self._uid,
            'ready_for_contracted_sale': True,
            'ready_for_contracted_sale_date': date.today(),
            'db_for_contracted_sale_tracker': json_data
        })
        return True

    def cron_check_for_contracted_sale_request_status(self):
        data = self.sudo().search([('ready_for_contracted_sale', '=', True), ('db_for_contracted_sale_tracker', '>', 0),
                                   ('cancellation_date', '=', False)])
        for r in data:
            r.check_for_contracted_sale_request_status()

    def check_for_contracted_sale_request_status(self):
        if self.ready_for_contracted_sale and self.db_for_contracted_sale_tracker != 0:
            api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
            conn = http.client.HTTPSConnection(api_key.api_url)
            headers = {'X-AppKey': api_key.api_app_key,
                       'X-AppId': api_key.api_app_id,
                       'Content-Type': api_key.api_content_type}
            conn.request("GET",
                         f"/VistaAdminAPI/rest/SOContract/GetSOContract?id={self.db_for_contracted_sale_tracker}", [],
                         headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            if json_data and json_data[0].get("STATUS") in ['1', '2']:
                vals = {
                    "db_for_contracted_sale_log": json_data[0].get("MESSAGELOG")
                }

                if json_data[0].get("STATUS") == '2':
                    vals.update({
                        'for_contracted_sale_user_id': False,
                        'ready_for_contracted_sale': False,
                        'ready_for_contracted_sale_date': False,
                        'db_for_contracted_sale_tracker': 0
                    })
                    msg = f"<p>Hi {self.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for conversion to Contracted Sale for the said SO was unable to process in our SAP system." \
                          f"due to the ff. reason/s: <em>{json_data[0].get('MESSAGELOG')}</em></p>"
                else:
                    msg = f"<p>Hi {self.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for conversion to Contracted Sale for the said SO has been successfully processed in our SAP system.</p>"
                    stage = self.env['property.sale.status'].search(
                        [('active', '=', True), ('name', '=', 'Contracted')], limit=1)
                    vals['stage_id'] = stage.id
                    vals['contracted_sale_date'] = (
                        datetime.strptime(json_data[0].get("CONTRACTDATETIME"), "%Y-%m-%d %H:%M:%S")).strftime(
                        "%Y-%m-%d")
                post_vars = {'partner_ids': [self.account_officer_user_id.partner_id.id]}
                subject = f"{self.subdivision_phase_id.brand} - Conversion to Contracted Sale stage {self.so_number}"
                self.message_post(body=msg, subject=subject, **post_vars)
                self.sudo().write(vals)
        return True

    def cron_check_cancellation_request_status(self):
        data = self.sudo().search(
            [('for_cancellation', '=', True), ('db_cancellation_tracker', '>', 0), ('cancellation_date', '=', False)])
        for r in data:
            r.check_cancellation_request_status()

    def check_cancellation_request_status(self):
        _logger.info(f"\n\nCompany: {self.env.company}\nContext: {self._context}\n\n")
        if self.for_cancellation and self.db_cancellation_tracker != 0:
            api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
            conn = http.client.HTTPSConnection(api_key.api_url)
            headers = {'X-AppKey': api_key.api_app_key,
                       'X-AppId': api_key.api_app_id,
                       'Content-Type': api_key.api_content_type}
            conn.request("GET", f"/VistaAdminAPI/rest/SOCancel/GetSOCancel?id={self.db_cancellation_tracker}", [],
                         headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            if json_data and json_data[0].get("STATUS") in ['1', '2']:
                vals = {
                    "db_cancellation_log": json_data[0].get("MESSAGELOG")
                }
                if json_data[0].get("STATUS") == '2':
                    vals.update({
                        'for_cancellation_user_id': False,
                        'for_cancellation': False,
                        'for_cancellation_date': False,
                        'cancellation_reason_id': False,
                        'before_cancelled_stage_id': False,
                        'db_cancellation_tracker': 0
                    })
                    msg = "<p>Hi ${object.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for account cancellation for the said SO was unable to process in our SAP system." \
                          f"due to the ff. reason/s: <em>{json_data[0].get('MESSAGELOG')}</em></p>"
                else:
                    vals['released_commission'] = True
                    msg = f"<p>Hi {self.account_officer_user_id.name},</p>" \
                          f"<br/><p>Please be informed that the request for account cancellation for the said SO has successfully processed in our SAP system.</p>"
                    stage = self.env['property.sale.status'].search(
                        [('active', '=', True), ('canceled', '=', True)], limit=1)
                    vals['stage_id'] = stage.id
                    vals['cancellation_date'] = (
                        datetime.strptime(json_data[0].get("CANCELDATETIME"), "%Y-%m-%d %H:%M:%S")).strftime(
                        "%Y-%m-%d")
                post_vars = {'partner_ids': [self.account_officer_user_id.partner_id.id]}
                subject = f"{self.subdivision_phase_id.brand} - Conversion to Contracted Sale stage {self.so_number}"
                self.message_post(body=msg, subject=subject, **post_vars)
                self.sudo().write(vals)
        return True

    def open_wizard(self):
        return {
            'name': 'my wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'property.document.submission',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'}

    def update_so_submitted_documents(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        conn = http.client.HTTPSConnection(api_key.api_url)
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        if self.so_number and self.company_id.sap_client_id:
            conn.request("GET",
                         f"/VistaAdminAPI/rest/DocsMasterData/GetDocs?VBELN={self.so_number}&MANDT={self.company_id.sap_client_id}",
                         [], headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            doc_obj = self.env['property.sale.required.document']
            required_documents = list()
            submitted_doc = list()
            for r in self.document_requirement_list_ids:
                required_documents.append(f"{r.group_code}{r.code}")
            for r in json_data:
                data_doc = f"{r.get('MNGRP')}{r.get('MNCOD')}"
                if data_doc in required_documents:
                    doc = doc_obj.sudo().search(
                        [('group_code', '=', r.get('MNGRP')), ('code', '=', r.get('MNCOD'))], limit=1)
                    if doc[:1]:
                        submitted_doc.append(doc.id)
            self.write({'sale_document_requirement_ids': [(6, 0, submitted_doc)]})
        return True

    @api.onchange('cancellation_reason_code')
    def _onchange_cancellation_reason_code(self):
        if self.cancellation_reason_code:
            cancel_reason = self.env['property.sale.cancellation.reason'].search(
                [('code', '=', str(self.cancellation_reason_code))], limit=1)
            if cancel_reason[:1]:
                self.cancellation_reason_id = cancel_reason.id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.company_code = self.company_id.code

    @api.onchange('company_code')
    def onchange_company_company_code(self):
        if self.company_code:
            company = self.env['res.company'].sudo().search([('code', '=', self.company_code)], limit=1)
            if company[:1]:
                self.company_id = company.id

    @api.onchange('customer_number')
    def onchange_customer_number(self):
        contact = self.env['res.partner']
        if self.customer_number:
            partner = contact.search([('partner_assign_number', '=', self.customer_number)], limit=1)
            self.partner_id = partner[:1] and partner.id or False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.customer_number = self.partner_id.partner_assign_number

    @api.onchange('be_code', 'block_lot', 'su_number')
    def onchange_property_detail(self):
        if self.be_code and self.block_lot and self.su_number:
            property_detail = self.env['property.detail'].search(
                [('be_code', '=', self.be_code), ('block_lot', '=', self.block_lot), ('su_number', '=', self.su_number)],
                limit=1)
            if property_detail[:1]:
                self.property_id = property_detail.id
                self.property_type = property_detail.property_type

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.block_lot = self.property_id.block_lot
            self.be_code = self.property_id.be_code
            self.su_number = self.property_id.su_number
            self.property_type = self.property_id.property_type

    @api.onchange('agent_unique_number')
    def onchange_agent_unique_number(self):
        contact = self.env['res.partner']
        if self.agent_unique_number:
            partner = contact.search([('sales_account_number', '=', self.agent_unique_number)], limit=1)
            self.agent_partner_id = partner[:1] and partner.id or False

    @api.model
    def create(self, vals):
        vals = self.check_data(vals)
        # if vals.get('stage_id'):
        #     if vals.get('property_type') and vals.get('property_type') == 'House & Lot':
        #         vals['property_type'] = 'House and Lot'
        #     if vals.get('property_type') and vals.get('property_type') == 'House only':
        #         vals['property_type'] = 'House Only'
        #     if vals.get('property_type') and not vals.get('property_type') in ['House and Lot', 'House Only', 'Condo',
        #                                                                        'Parking Condo', 'Lot Only',
        #                                                                        'Parking Only', 'Others']:
        #         vals['property_type'] = 'Others'
        #     vals['stage_id'] = int(vals.get('stage_id'))
        #     sub_stage = self.env['property.sale.sub.status'].search(
        #         [('active', '=', True), ('sub_parent_id', '=', vals.get('stage_id'))], order='sequence asc')
        #     vals['sub_stage_id'] = sub_stage[:1] and sub_stage[0].id or False
        #     vals['moved_sub_stage_datetime'] = sub_stage[:1] and datetime.now() or False
        #     assigned_person = self.env['property.status.assigned.person'].search(
        #         [('state_id', '=', vals.get('stage_id')), ('be_code', '=', vals.get('be_code'))], limit=1)
        #     if assigned_person[:1]:
        #         vals[
        #             'account_officer_user_id'] = assigned_person.account_officer_user_id and assigned_person.account_officer_user_id.id or False
        #         vals[
        #             'collection_officer_user_id'] = assigned_person.collection_officer_user_id and assigned_person.collection_officer_user_id.id or False
        # if vals.get('account_officer_user_id'):
        #     vals['ao_assigned_date'] = date.today()
        # if vals.get('collection_officer_user_id'):
        #     vals['co_assigned_date'] = date.today()
        # if vals.get('account_officer_user_id') or vals.get('collection_officer_user_id'):
        #     data = {
        #         'account_officer_user_id': vals.get('account_officer_user_id'),
        #         'collection_officer_user_id': vals.get('collection_officer_user_id'),
        #         'stage_id': vals.get('stage_id'),
        #         'sub_stage_id': vals.get('sub_stage_id'),
        #         'user_id': self._uid,
        #     }
        #     vals['assignment_log_ids'] = [(0, 0, data)]
        # vals['moved_stage_datetime'] = datetime.now()
        res = super(PropertyAdminSale, self).create(vals)
        res.update_so_submitted_documents()
        res._onchange_cancellation_reason_code()
        res.onchange_company_company_code()
        res.onchange_customer_number()
        res.onchange_property_detail()
        res.onchange_agent_unique_number()
        return res

    def get_account_cancellation_reason(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        conn = http.client.HTTPSConnection(api_key.api_url)
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn.request("GET", f"/VistaAdminAPI/rest/CancelReason/GetCancelReason", [], headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        reason_data = list()
        for r in json_data:
            found = False
            for i in reason_data:
                if i.get('name') == r.get("BEZEI") and i.get('code') == r.get("ABGRU"):
                    found = True
                    break
            if not found:
                reason_data.append({
                    'name': r.get("BEZEI"),
                    'code': r.get("ABGRU"),
                    'active': True,
                })
        for r in reason_data:
            self.env['property.sale.cancellation.reason'].create(r)
        return True

    def get_document_requirement(self):
        api_key = self.env.ref('admin_api_connector.admin_api_key_config_data')
        locally_employed = self.env.ref('contact_personal_information.employment_locally_employed')
        self_employed = self.env.ref('contact_personal_information.employment_self_employed')
        ofw = self.env.ref('contact_personal_information.employment_ofw')
        retiree = self.env.ref('contact_personal_information.employment_retiree_pensioner')
        foreigners = self.env.ref('contact_personal_information.employment_foreigners')
        conn = http.client.HTTPSConnection(api_key.api_url)
        headers = {'X-AppKey': api_key.api_app_key,
                   'X-AppId': api_key.api_app_id,
                   'Content-Type': api_key.api_content_type}
        conn.request("GET", f"/VistaAdminAPI/rest/DocsLookup/GetDocs", [], headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        locally_employed_data = list()
        self_employed_data = list()
        ofw_data = list()
        retiree_data = list()
        foreigners_data = list()
        standard_data = list()
        other_data = list()
        for r in json_data:
            found = False
            if r.get("CODEGRUPPE") == 'LOCL':
                for i in locally_employed_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    locally_employed_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'employment_status_id': locally_employed.id,
                        'submitted_by_buyer': True
                    })
            elif r.get("CODEGRUPPE") == 'SELF':
                for i in self_employed_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    self_employed_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'employment_status_id': self_employed.id,
                        'submitted_by_buyer': True
                    })
            elif r.get("CODEGRUPPE") == 'OFWR':
                for i in ofw_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    ofw_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'employment_status_id': ofw.id,
                        'submitted_by_buyer': True
                    })
            elif r.get("CODEGRUPPE") == 'PNSR':
                for i in retiree_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    retiree_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'employment_status_id': retiree.id,
                        'submitted_by_buyer': True
                    })
            elif r.get("CODEGRUPPE") == 'FRNR':
                for i in foreigners_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    foreigners_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'employment_status_id': foreigners.id,
                        'submitted_by_buyer': True
                    })
            elif r.get("CODEGRUPPE") == 'STND':
                for i in standard_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    standard_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                        'submitted_by_buyer': True
                    })
            else:
                for i in other_data:
                    if i.get('name') == r.get("KURZTEXT") and i.get('group_code') == r.get("CODEGRUPPE") and i.get(
                            'code') == r.get("CODE"):
                        found = True
                        break
                if not found:
                    other_data.append({
                        'name': r.get("KURZTEXT"),
                        'group_code': r.get("CODEGRUPPE"),
                        'code': r.get("CODE"),
                        'active': True,
                    })
        doc_obj = self.env['property.sale.required.document']
        for r in locally_employed_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in self_employed_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in ofw_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in retiree_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in foreigners_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in standard_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        for r in other_data:
            doc = doc_obj.search(
                [('group_code', '=', r.get('group_code')), ('code', '=', r.get('code'))], limit=1)
            if doc[:1]:
                doc.write(r)
            else:
                doc_obj.create(r)
        return True


class PropertySalesAssignmentLog(models.Model):
    _name = 'property.sale.assignment.log'
    _description = "Assignment Logs"
    _rec_name = 'property_sale_id'

    property_sale_id = fields.Many2one('property.admin.sale', index=True)
    account_officer_user_id = fields.Many2one('res.users', string="Account Officer",
                                              help="Sales Admin Account Officer Assigned")
    collection_officer_user_id = fields.Many2one('res.users', string="Collection Officer",
                                                 help="Collection Account Officer Assigned")
    stage_id = fields.Many2one('property.sale.status', string="Status")
    sub_stage_id = fields.Many2one('property.sale.sub.status', string="Sub-Status")
    user_id = fields.Many2one('res.users', string="Moved By")


class PropertySalesStatusLog(models.Model):
    _name = 'property.sale.status.log'
    _description = "Status log"
    _rec_name = 'property_sale_id'

    status = fields.Char(string="Current Status")
    status_from = fields.Char(string="Status From")
    property_sale_id = fields.Many2one('property.admin.sale', index=True)
    status_type = fields.Selection([('Status', 'Status'), ('Sub-status', 'Sub-status')], string="Type")
    account_officer_user_id = fields.Many2one('res.users', string="Account Officer",
                                              help="Sales Admin Account Officer Assigned")
    collection_officer_user_id = fields.Many2one('res.users', string="Collection Officer",
                                                 help="Collection Account Officer Assigned")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date To")
    total_days = fields.Float(string="Total Days")
    user_id = fields.Many2one('res.users', string="Moved By")


class PropertyDocumentSubmissionLine(models.Model):
    _name = 'property.document.submission.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Validate document submitted"
    _rec_name = 'document_id'

    property_sale_id = fields.Many2one('property.admin.sale', index=True)
    document_id = fields.Many2one('property.sale.required.document', string="Document Name", required=True)
    validation_date = fields.Date(string="Validation Date", default=fields.Date.today(), required=True)
    expiry_date = fields.Date(string="Expiry Date", help="Indicate if the document has an expiry date")
    note = fields.Text(string="Notes")

    def write(self, vals):
        # _logger.info(f"\n\n{self.env.ref('property_admin_monitoring.property_document_submission_line')}\n\n")
        if 'expiry_date' in vals and vals['expiry_date']:
            act_type_id = self.env['mail.activity.type'].search(
                [('name', 'ilike', 'Expiring Documents')], limit=1)
            if not act_type_id[:1]:
                act_type_id = self.env['mail.activity.type'].create({'name': 'Expiring Documents'})
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('property_admin_monitoring.model_property_document_submission_line').id,
                'res_id': self.id,
                'user_id': self._uid,
                'activity_type_id': act_type_id.id,
                'date_deadline': vals.get('expiry_date'),
                'note': vals.get('note')
            })
        return super(PropertyDocumentSubmissionLine, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(PropertyDocumentSubmissionLine, self).create(vals)
        if 'expiry_date' in vals and vals['expiry_date']:
            act_type_id = self.env['mail.activity.type'].search(
                [('name', 'ilike', 'Expiring Documents')], limit=1)
            if not act_type_id[:1]:
                act_type_id = self.env['mail.activity.type'].create({'name': 'Expiring Documents'})
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('property_admin_monitoring.model_property_document_submission_line').id,
                'res_id': res.id,
                'user_id': self._uid,
                'activity_type_id': act_type_id.id,
                'date_deadline': vals.get('expiry_date'),
                'note': vals.get('note')
            })
        return res
