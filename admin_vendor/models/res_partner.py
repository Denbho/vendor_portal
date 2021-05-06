# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_EVALUATION = [
    ('pending', 'Pending'),
    ('ongoing_review', 'Ongoing review'),
    ('approved', 'Approved'),
]


class ResPartnerAffiliation(models.Model):
    _name = 'res.partner.affiliation'
    _description = "Contact Affiliations"

    name = fields.Char(string="Company/Subsidiary", required=True)
    contact_partner_id = fields.Many2one('res.partner', string="Contact Details")
    email = fields.Char(string="Email")
    relationship = fields.Char(string="Relationship")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.onchange('email')
    def onchange_email(self):
        if self.email:
            contact = self.env['res.partner'].sudo().search([('email', '=', self.email)])
            if contact[:1]:
                self.contact_partner_id = contact.id


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_show_accredit_button(self):
        for rec in self:
            rec.check_date_prebid_postbid = True
            current_date = fields.Date.today()
            show_accredit = False
            if rec.end_date:
                if current_date >= rec.end_date:
                    show_accredit = True
            else:
                show_accredit = True
            self.show_accredit_button = show_accredit

    affiliated_subsidiary_comp_ids = fields.Many2many(comodel_name='res.partner',
                                                      relation='affiliated_subsidiary_comp_rel',
                                                      column1='affiliated_subsidiary_comp_id',
                                                      column2='affiliated_subsidiary_comp_id2',
                                                      string='Affiliated/Subsidiary Companies')
    affiliated_contact_ids = fields.One2many('res.partner.affiliation', 'partner_id',
                                             string="Affiliated/Subsidiary Companies")
    registration_date = fields.Date(string='Registration Date', track_visibility="always")
    product_category_ids = fields.Many2many('product.category', string='Product Categories')
    product_service_offered_line = fields.One2many('product.service.offered', 'partner_id',
                                                   string='Products/Services Offered')
    document_ids = fields.Many2many('document.requirement', string='Documents')
    for_accreditation = fields.Boolean(string='For Accreditation', track_visibility="always")
    accredited = fields.Boolean(string='For Accredited', track_visibility="always")
    date_accredited = fields.Date(string='Date Accredited', track_visibility="always")
    start_date = fields.Date(string='Start Date', track_visibility="always")
    end_date = fields.Date(string='End Date', track_visibility="always")
    evaluation_period = fields.Date(string='Evaluation Period', track_visibility="always")
    overall_assessment = fields.Float(string='Overall Assessment', track_visibility="always")
    extend_result = fields.Boolean(string='Extend Result to Vendor?', track_visibility="always")
    evaluation_count = fields.Integer(compute="_get_evaluation_count")
    supplier_number = fields.Char('Supplier No.')

    _sql_constraints = [
        ('supplier_number_key', 'unique(supplier_number)',  "You can't have two vendors with the same supplier number !")
    ]

    def name_get(self):
        res = []
        for partner in self:
            name = partner._get_name()
            if partner.supplier_rank >= 1:
                accredit_str = partner.accredited and 'Accredited' or 'For Accreditation'
                name += ' [' + accredit_str + ']'
            res.append((partner.id, name))
        return res

    def compute_for_accreditation(self):
        accredited = self.sudo().search([('accredited', '=', True)])
        for r in accredited:
            vals = {}
            if r.end_date <= date.today() and r.supplier_rank >= 1:
                vals.update({
                    'for_accreditation': True,
                    'accredited': False
                })
                r.send_admin_email_notif('re_accreditation_request', 'Re-Accreditation Request', r.email, 'res.partner')
            if vals:
                r.sudo().write(vals)

    def create_evaluation_accreditation(self):
        data = self.env['partner.evaluation'].sudo().create({
            'partner_id': self.id
        })
        self.sudo().write({'for_accreditation': True})
        return data

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if vals.get('registration_date') and (not vals.get('start_date') or not vals.get('date_accredited')):
            res.create_evaluation_accreditation()
        elif vals.get('end_date') and vals.get('end_date') <= date.today():
            res.create_evaluation_accreditation()
        return res

    def _compute_show_accredit_button(self):
        for rec in self:
            current_date = fields.Date.today()
            show_accredit = False
            if rec.end_date:
                if current_date >= rec.end_date:
                    show_accredit = True
            else:
                show_accredit = True
            self.show_accredit_button = show_accredit

    def _get_evaluation_count(self):
        for r in self:
            r.evaluation_count = self.env['partner.evaluation'].search_count([('partner_id', '=', r.id)])

    def action_accredit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Accredit'),
            'res_model': 'vendor.accredit',
            'target': 'new',
            'view_mode': 'form',
        }

    def action_evaluate(self):
        self.ensure_one()
        return {
            'name': _('Evaluations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.evaluation',
            'domain': [('partner_id', '=', self.id)],
            'target': 'current',
            'context': {'default_partner_id': self.id},
        }


class PartnerEvaluationLine(models.Model):
    _name = "partner.evaluation.line"
    _inherit = "vendor.evaluation.line"
    _description = "Partner Evaluation Line"

    name = fields.Char(string="Description")
    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation", index=True,
                                            ondelete='cascade')
    score = fields.Float(string="Score", compute='_compute_average', store=True)

    @api.depends(
        'partner_evaluation_id.evaluator_line',
        'partner_evaluation_id.evaluator_line.type',
        'partner_evaluation_id.evaluator_line.evaluation_line',
        'partner_evaluation_id.evaluator_line.evaluation_line.score')
    def _compute_average(self):
        for rec in self:
            evaluation_ids = self.env['partner.evaluator.line'].search(
                [('evaluation_id', '=', rec.id), ('display_type', '=', False)])
            score_average = 0
            line_cnt = 0
            for line in evaluation_ids:
                score_average += line.score
                line_cnt += 1
            rec.score = score_average and (score_average / line_cnt) or 0


class PartnerEvaluator(models.Model):
    _name = "partner.evaluator"
    _description = "Partner Evaluator"

    name = fields.Char(related='evaluator_id.name', string='Name')
    evaluator_id = fields.Many2one('res.users', string='Evaluator', default=lambda self: self.env.user, required=True)
    partner_evaluation_id = fields.Many2one('partner.evaluation', string="Partner Evaluation")
    evaluation_line = fields.One2many('partner.evaluator.line', 'partner_evaluator_id', string='Evaluation', copy=True)
    type = fields.Selection([('commercial', "Commercial"), ('technical', "Technical")], string='Evaluation Type')

    @api.onchange('type')
    def _onchange_type(self):
        eval_type = self.type
        if self.evaluation_line:
            self.evaluation_line.unlink()
        if eval_type:
            for rec in self.partner_evaluation_id:
                default_eval_entries = rec.evaluation_line
                if eval_type == "commercial":
                    default_eval_entries = rec.commercial_evaluation_line
                self.evaluation_line = [
                    (0, 0, line._prepare_evaluation_criteria(eval_type))
                    for line in default_eval_entries
                ]
        self.type = eval_type


class PartnerEvaluatorLine(models.Model):
    _name = "partner.evaluator.line"
    _inherit = "vendor.evaluator.line"
    _description = "Partner Evaluator Line"

    partner_evaluator_id = fields.Many2one('partner.evaluator', string="Evaluator", index=True, ondelete='cascade')
    evaluation_id = fields.Many2one('partner.evaluation.line', string='Partner Evaluation Line')


class VendorAccredit(models.TransientModel):
    _name = "vendor.accredit"
    _description = "Accredit"

    date_accredited = fields.Date(string='Date Accredited', default=fields.Date.today(), required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def action_confirm_accredit(self):
        context = self.env.context
        active_model = context['active_model']
        active_id = context['active_id']
        active_entry = self.env[active_model].browse(active_id)
        active_entry.write({
            'date_accredited': self.date_accredited,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'for_accreditation': False
        })


class ProductServiceOffered(models.Model):
    _name = 'product.service.offered'
    _description = 'Products/Services Offered'

    name = fields.Char(string="Product/Service Description", required=True)
    product_service = fields.Char(string="Product/Service")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    sequence = fields.Integer(string='Sequence', default=10)
    price = fields.Float(string="Price")
    product_category_id = fields.Many2one('product.category', string='Product Category')
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.", string='Display Type')


class PartnerEvaluation(models.Model):
    _name = "partner.evaluation"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "resource.mixin", "document.default.approval", "admin.email.notif"]
    _description = "Partner Evaluation"

    def _compute_evaluator_count(self):
        for rec in self:
            self.evaluator_count = len(rec.evaluator_line)

    @api.model
    def default_get(self, default_fields):
        res = super(PartnerEvaluation, self).default_get(default_fields)
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', True)],
                                                                              limit=1)
        res.update({
            'evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('technical')) for line in
                default_template_data.technical_evaluation_line
            ],
            'commercial_evaluation_line': [
                (0, 0, line._prepare_evaluation_criteria('commercial')) for line in
                default_template_data.commercial_evaluation_line
            ],
            'required_document_accreditation_requirement_ids': [
                (6, 0, [line.id for line in default_template_data.document_accreditation_requirement_ids])],
            'technical_valuation_weight': default_template_data.technical_valuation_weight,
            'commercial_valuation_weight': default_template_data.commercial_valuation_weight
        })
        return res

    name = fields.Char(string="Accreditation Number", copy=False, readonly=True, index=True,
                       default=lambda self: _('New'), track_visibility="always")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, track_visibility="always")
    evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id', string='Technical Evaluation',
                                      copy=True, domain=[('type', '=', 'technical')])
    commercial_evaluation_line = fields.One2many('partner.evaluation.line', 'partner_evaluation_id',
                                                 string='Commercial Evaluation', copy=True,
                                                 domain=[('type', '=', 'commercial')])

    evaluator_line = fields.One2many('partner.evaluator', 'partner_evaluation_id', string='Evaluator Line')
    evaluator_count = fields.Integer(compute='_compute_evaluator_count', string='Evaluator Count')
    required_document_accreditation_requirement_ids = fields.Many2many('document.requirement',
                                                                       'evaluation_required_document_requirement_rel',
                                                                       string='Documents',
                                                                       readonly=False,
                                                                       states={'approved': [('readonly', True)]})
    document_accreditation_requirement_ids = fields.Many2many('document.requirement',
                                                              'evaluation_document_requirement_rel', string='Documents',
                                                              readonly=False, states={'approved': [('readonly', True)]})
    accreditation_validity = fields.Integer(string="Accreditation Validity", default=2, track_visibility="always",
                                            readonly=False, states={'approved': [('readonly', True)]})
    start_date = fields.Date(string='Start Date', track_visibility="always", readonly=False,
                             states={'approved': [('readonly', True)]})
    end_date = fields.Date(string='End Date', readonly=True, force_save=True)
    accreditation_remarks = fields.Html(string="Accreditation Remarks", readonly=False,
                                        states={'approved': [('readonly', True)]})

    technical_valuation_weight = fields.Float(string="Technical Valuation Weight", track_visibility="always",
                                              default=1, readonly=False, states={'approved': [('readonly', True)]})
    commercial_valuation_weight = fields.Float(string="Commercial Valuation Weight", track_visibility="always",
                                               default=1, readonly=False, states={'approved': [('readonly', True)]})
    technical_valuation_score = fields.Float(string="Technical Valuation Weight", store=True,
                                             compute="_get_valuation_score")
    commercial_valuation_score = fields.Float(string="Commercial Valuation Weight", store=True,
                                              compute="_get_valuation_score")
    overall_score = fields.Float(string="Overall Evaluation Score", store=True, compute="_get_valuation_score")
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    @api.depends('evaluation_line', 'evaluation_line.weight', 'evaluation_line.score',
                 'commercial_evaluation_line', 'commercial_evaluation_line.weight', 'commercial_evaluation_line.score',
                 'technical_valuation_weight', 'commercial_valuation_weight')
    def _get_valuation_score(self):
        for r in self:
            total_technical_valuation_weight = sum(i.weight for i in r.evaluation_line)
            total_commercial_valuation_weight = sum(i.weight for i in r.commercial_evaluation_line)
            total_technical_valuation_score = sum(
                (i.weight / total_technical_valuation_weight) * i.score if i.weight > 0 and total_technical_valuation_weight > 0 else 0
                for i in r.evaluation_line)
            total_commercial_valuation_score = sum(
                (i.weight / total_commercial_valuation_weight) * i.score if i.weight > 0 and total_commercial_valuation_weight > 0 else 0
                for i in r.commercial_evaluation_line)
            overall_weight = sum([r.technical_valuation_weight, r.commercial_valuation_weight])
            overall_score = r.technical_valuation_weight > 0 and overall_weight and (r.technical_valuation_weight / overall_weight) * total_technical_valuation_score or 0
            overall_score += r.commercial_valuation_weight > 0 and overall_weight and (r.commercial_valuation_weight / overall_weight) * total_commercial_valuation_score or 0
            r.technical_valuation_score = total_technical_valuation_score
            r.commercial_valuation_score = total_commercial_valuation_score
            r.overall_score = overall_score

    @api.onchange('start_date', 'accreditation_validity')
    def onchange_start_date(self):
        if self.start_date and self.accreditation_validity:
            self.end_date = self.start_date + relativedelta(years=self.accreditation_validity)

    def approve_request(self):
        vals = {
            'state': 'approved',
            'approved_by': self._uid,
            'approved_date': datetime.now()
        }
        start_date = self.start_date
        if not start_date:
            start_date = date.today()
            vals['start_date'] = start_date
        vals['end_date'] = start_date + relativedelta(years=self.accreditation_validity)
        self.partner_id.write({
            'date_accredited': date.today(),
            'start_date': start_date,
            'end_date': start_date + relativedelta(years=self.accreditation_validity),
            'for_accreditation': False,
            'accredited': True,
        })
        self.send_admin_email_notif('accreditation_result', 'Accreditation Result', self.partner_id.email, 'partner.evaluation')
        return self.write(vals)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('vendor.accreditation')
        res = super(PartnerEvaluation, self).create(vals)
        res.send_admin_email_notif('accreditation_request', 'Accreditation Request', self.partner_id.email, 'partner.evaluation')
        return res

    def write(self, vals):
        res = super(PartnerEvaluation, self).write(vals)
        if 'document_accreditation_requirement_ids' in vals:
            if len(self.document_accreditation_requirement_ids) == len(self.required_document_accreditation_requirement_ids):
                self.send_admin_email_notif('accreditation_submitted', 'Accreditation Submitted', self.partner_id.email, 'partner.evaluation')
        return res

    def action_view_evaluator(self):
        self.ensure_one()
        return {
            'name': _('Evaluator'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'partner.evaluator',
            'domain': [('partner_evaluation_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_partner_evaluation_id': self.id,
                'default_type': 'technical',
            },
        }


class PurchaseBid(models.Model):
    _inherit = "purchase.bid"

    def _default_technical_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', False)],
                                                                              limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('technical')) for line in rec.technical_evaluation_line
            ]
        return res

    def _default_commercial_evaluation_line(self):
        res = []
        default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', False)],
                                                                              limit=1)
        for rec in default_template_data:
            res = [
                (0, 0, line._prepare_evaluation_criteria('commercial')) for line in rec.commercial_evaluation_line
            ]
        return res
