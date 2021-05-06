# -*- coding: utf-8 -*-
{
    'name': "Admin Purchase Bid",
    'summary': """
            Admin Purchase Bid
        """,
    'author': "Ruel Costob",
    'category': 'Bid',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_contracts_and_agreements',
        'admin_purchase_requisition',
        'admin_email_notif',
        'hr',
        ],
    'data': [
        'security/ir.model.access.csv',
        'report/purchase_bid_report_template.xml',
        'report/purchase_bid_report.xml',
        'views/bid_view.xml',
        'views/contracts_and_agreements_view.xml',
        'views/purchase_requisition_view.xml',
        'data/bid_cron_view.xml',
        'data/mail_template_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
