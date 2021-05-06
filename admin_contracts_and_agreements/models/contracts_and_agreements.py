# -*- coding: utf-8 -*-
import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime

_STATES = [
    ('draft', 'Draft'),
    ('waiting_to_verify', 'Waiting to verify'),
    ('verified', 'Verified'),
    ('waiting_for_approval', 'Waiting for approval'),
    ('approved', 'Approved'),
    ('cancelled', 'Cancelled')
]

_SAP_DELIVERY_STATUS = [
    ('undelivered','Undelivered'),
    ('partially_delivered','Partially Delivered'),
    ('fully_delivered','Fully Delivered'),
]

class ContractsAndAgreements(models.Model):
    _name = "contracts.and.agreements"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Contracts and Agreements"
    _order = 'id desc'

    name = fields.Char(string='Contract', required=True, copy=False, default=lambda self: _('New'), readonly=True)
    ref_no = fields.Char(string='Ref. No.', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, track_visibility='onchange')
    contract_agreement_name = fields.Char(string='Contract/Agreement Name', track_visibility='onchange', required=True)
    contract_date_created = fields.Date(string="Contract/Agreement Creation Date", default=fields.Date.today(), track_visibility='onchange')
    purchasing_officer = fields.Many2one('res.users', string='Purchasing Officer', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange')
    start_date = fields.Date(string="Start Date", track_visibility='onchange', required=True)
    end_date = fields.Date(string="End Date", track_visibility='onchange')
    total_con_agreement_amt = fields.Float(string="Total Contract/Agreement Amount", track_visibility='onchange')
    contract_progress = fields.Float(compute='_compute_progress', store=True, string="Contract Progress")
    created_by = fields.Many2one('res.users', string="Created by", track_visibility='onchange', readonly=True)
    created_date = fields.Date('Date Created', track_visibility='onchange', readonly=True)
    verified_by = fields.Many2one('res.users', string="Verified by", track_visibility='onchange', readonly=True)
    verified_date = fields.Date('Date Verified', track_visibility='onchange', readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved by", track_visibility='onchange', readonly=True)
    approved_date = fields.Date('Date Approved', track_visibility='onchange', readonly=True)
    notice_to_proceed_sent = fields.Boolean('Notice to Proceed Sent', copy=False)
    company_allocation_count = fields.Integer(compute='_compute_company_allocation_count', string='Company Allocation Count')
    total_comp_allocation = fields.Float(compute='_compute_company_allocation_total', store=True, compute_sudo=True, string='Total Company Allocation')
    po_line = fields.One2many('purchase.order', 'contracts_agreement', string='PO Associated')
    inclusion_line = fields.One2many('contracts.and.agreements.inclusion', 'contracts_agreement', string='Inclusion')
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    state = fields.Selection(selection=_STATES,
                             string='Contract/Agreement Status',
                             index=True,
                             track_visibility='onchange',
                             required=True,
                             copy=False,
                             default='draft',)

    def action_send_notice_to_proceed(self):
        '''
        This function opens a window to compose an email, with the edi bid template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('admin_contracts_and_agreements', 'email_template_edi_contract')[1]
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        partner_ids = [self.partner_id.id]
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'contracts.and.agreements',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_notice_to_proceed_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'default_partner_ids': partner_ids,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_notice_to_proceed_as_sent'):
            self.write({'notice_to_proceed_sent': True})
        return super(ContractsAndAgreements, self).message_post(**kwargs)

    def action_submit(self):
        self.state = 'waiting_to_verify'
        self.created_by = self.env.user.id
        self.created_date = fields.Date.today()

    def action_verify(self):
        self.state = 'verified'
        self.verified_by = self.env.user.id
        self.verified_date = fields.Date.today()

    def action_request_approval(self):
        self.state = 'waiting_for_approval'

    def action_approve(self):
        self.state = 'approved'
        self.approved_by = self.env.user.id
        self.approved_date = fields.Date.today()

    def action_cancel(self):
        self.state = 'cancelled'

    @api.depends('total_comp_allocation', 'total_con_agreement_amt')
    def _compute_progress(self):
        progress = 0
        if self.total_con_agreement_amt > 0:
            progress = (self.total_comp_allocation / self.total_con_agreement_amt) * 100
        self.contract_progress = progress

    def _compute_company_allocation_count(self):
        for record in self:
            record.company_allocation_count = len(self.env['purchase.order.line'].search([('contracts_agreement','=',record.id)]))

    @api.depends('po_line', 'po_line.amount_total')
    def _compute_company_allocation_total(self):
        for record in self:
            total_amount = 0
            for line in self.po_line:
                total_amount += line.amount_total
            self.total_comp_allocation = total_amount

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('contracts.and.agreements') or 'New'
        res = super(ContractsAndAgreements, self).create(values)
        return res

    def action_view_company_allocation(self):
        self.ensure_one()
        return {
            'name': _('Company Allocation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'res_model': 'purchase.order.line',
            'domain': [('contracts_agreement','=', self.id),('product_qty','>',0)],
            'target': 'current',
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contracts_agreement = fields.Many2one('contracts.and.agreements', string='Contract/Agreement')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    contracts_agreement = fields.Many2one(related="order_id.contracts_agreement")


class ContractsAndAgreementsInclusion(models.Model):
    _name = "contracts.and.agreements.inclusion"
    _description = "Contracts and Agreements Inclusion"
    _rec_name = 'product_id'

    contracts_agreement = fields.Many2one('contracts.and.agreements', string='Contract/Agreement')
    product_id = fields.Many2one('product.product', 'Material', required=True)
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.price
