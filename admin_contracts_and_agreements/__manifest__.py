# -*- coding: utf-8 -*-
{
    'name': "Vendor Contracts and Agreements",
    'summary': """
            Contracts and Agreements
        """,
    'author': "Ruel Costob",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_purchase_order',
        ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/contracts_and_agreements_view.xml',
        'data/mail_template_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
