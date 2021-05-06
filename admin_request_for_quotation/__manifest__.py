# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Quotation",
    'summary': """
        Vendor Request For Quotation Management""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'product',
        'purchase',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'wizard/select_rfq_vendor.xml',
        'views/rfq.xml'
    ],
    'installable': True,
    'auto_install': False,
}
