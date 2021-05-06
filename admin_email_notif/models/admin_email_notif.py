# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AdminEmailNotif(models.Model):
    _name = 'admin.email.notif'

    def get_notif_body(self, type):
        # Share url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        mail_body = ""
        if type == "accreditation_result":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Congratulations '+self.partner_id.name+'!</b><br/><br/>\
                            You have successfully qualified as an accredited supplier of '+self.env.company.name+'.<br/>\
                            Please expect to receive and accept purchase orders from us.<br/><br/>\
                            In the meantime, please explore the features of the Vendor Hub with the following  instructional videos and manuals:<br/>\
                            <span style="margin-left: 15px;">• Navigating Vendor Hub</span><br/>\
                            <span style="margin-left: 15px;">• Updating your profile</span><br/>\
                            <span style="margin-left: 15px;">• Monitoring purchase orders and deliveries</span><br/>\
                            <span style="margin-left: 15px;">• Uploading sales invoices, delivery receipts and official receipts</span><br/>\
                            <span style="margin-left: 15px;">• Monitoring billing payment status</span><br/><br/>\
                            We also conduct online training programs. We will inform you of the next schedule so you can attend.\
                            If you have any queries, you may contact us at <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "accreditation_request":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            '+self.env.company.name+' is pleased to invite you to be an accredited supplier of the Company. \
                            You may proceed with the accreditation process through the Vendor Hub. \
                            Kindly submit the following requirements.<br/><br/>'
            for docs_line in self.required_document_accreditation_requirement_ids:
                mail_body += '<span style="margin-left: 15px;">• '+docs_line.name+'</span><br/>'
            mail_body += '<br/>Please click the link below to submit the accreditation requirements.<br/><br/>[link]<br/><br/>\
                            If you encounter any issue during the process, you may contact us at \
                            <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "re_accreditation_request":
            default_template_data = self.env['vendor.evaluation.template'].search([('vendor_accreditation', '=', True)], limit=1)
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.name+',</b><br/><br/>\
                            Our records show that your accreditation has already expired as of today '+self.end_date.strftime("%B %d, %Y")+'. \
                            Kindly submit the following requirements.<br/><br/>'
            for line in default_template_data.document_accreditation_requirement_ids:
                mail_body += '<span style="margin-left: 15px;">• '+line.name+'</span><br/>'
            mail_body += '<br/>Please click the link below to complete your re-accreditation requirements.<br/><br/>[link]<br/><br/>\
                            If you encounter any issue on the re-accreditation, you may contact us at \
                            <a href="mailto: procurement.sourcing@camella.com.ph">procurement.sourcing@camella.com.ph</a>.<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "accreditation_submitted":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.partner_id.name+',</b><br/><br/>\
                            Thank you for completing the accreditation requirements through the Vendor Hub!<br/>\
                            We will review and validate your submission and let you know should there be additional requirements. <br/>\
                            We look forward to developing a mutually beneficial relationship with you!<br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        elif type == "bid_evaluation":
            mail_body += '<div style="margin: 0px; padding: 0px; font-size: 16px;"><p><br/>\
                            <b>Dear '+self.evaluator_id.name+',</b><br/><br/>\
                            You are selected as the evaluator for vendor '+ self.vendor_bid_id.partner_id.name +' \
                            on bid reference '+ self.bid_id.name +'.Please click the link below to evaluate the vendor.\
                            <br/><br/><a href="'+base_url+'">'+base_url+'</a><br/><br/><br/>\
                            Regards,<br/>'+self.env.company.name+'</p></div>'
        return mail_body

    def send_admin_email_notif(self, type, mail_subject, email_to, model):
        mail_body = self.get_notif_body(type)
        mail_values = {
            'subject': mail_subject,
            'email_to': email_to,
            'body_html': mail_body,
            'model': model,
            'res_id': self.id,
        }
        self.message_post(body=mail_body)
        return self.env['mail.mail'].create(mail_values).send()
