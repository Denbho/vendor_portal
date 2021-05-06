# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta, time


class DocumentDefaultApproval(models.Model):
    _name = 'document.default.approval'

    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Waiting for Confirmation'),
                              ('confirmed', 'Waiting for Verification'),
                              ('verified', 'Waiting for Approval'),
                              ('approved', 'Approved'),
                              ('canceled', 'Cancelled')], string="Status",
                             default='draft', readonly=True, copy=False, track_visibility="always")
    submitted_by = fields.Many2one('res.users', string="Submitted By", readonly=True)
    submitted_date = fields.Datetime('Submitted Date', readonly=True)
    verified_by = fields.Many2one('res.users', string="Verified By", readonly=True)
    verified_date = fields.Datetime('Verified Date', readonly=True)
    confirmed_by = fields.Many2one('res.users', string="Confirmed By", readonly=True)
    confirmed_date = fields.Datetime('Confirmed Date', readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    canceled_by = fields.Many2one('res.users', string="Cancelled By", readonly=True)
    canceled_date = fields.Datetime('Cancelled Date', readonly=True)

    def submit_request(self):
        return self.write({
                    'state': 'submitted',
                    'submitted_by': self._uid,
                    'submitted_date': datetime.now()
                })

    def confirm_request(self):
        return self.write({
                    'state': 'confirmed',
                    'confirmed_by': self._uid,
                    'confirmed_date': datetime.now()
                })

    def verify_request(self):
        return self.write({
                    'state': 'verified',
                    'verified_by': self._uid,
                    'verified_date': datetime.now()
                })

    def approve_request(self):
        return self.write({
                    'state': 'approved',
                    'approved_by': self._uid,
                    'approved_date': datetime.now()
                })

    def cancel_request(self):
        return self.write({
                    'state': 'canceled',
                    'canceled_by': self._uid,
                    'canceled_date': datetime.now()
                })

    def reset_to_draft_request(self):
        return self.write({
                    'state': 'draft',
                })
