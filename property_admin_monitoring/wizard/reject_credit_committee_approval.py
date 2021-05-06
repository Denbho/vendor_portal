from odoo import fields, models, api


class PropertySaleRejectCreditCommitteeApproval(models.TransientModel):
    _name = 'property.sale.reject.credit.committee.approval'
    _description = 'Reject Credit committee Approval'

    rejecting_reason_id = fields.Many2one('property.sale.cancellation.reason', string="Rejecting Reason", required=True)
    rejecting_notes = fields.Text(string="Rejecting Notes")

    def request_reject(self):
        crecom = self.env['property.sale.credit.committee.approval'].browse(self._context.get('active_id'))
        crecom.write({
            'rejecting_reason_id': self.rejecting_reason_id.id,
            'rejecting_notes': self.rejecting_notes,
            'submitted_by': self._uid,
            'submitted_date': fields.datetime.now(),
            'state': 'rejected'
        })
        return {'type': 'ir.actions.act_window_close'}
