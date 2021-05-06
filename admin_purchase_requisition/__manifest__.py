# -*- coding: utf-8 -*-
{
    'name': "Admin Purchase Requisition",
    'summary': """
            Admin Purchase Requisition
        """,
    'author': "Ruel Costob",
    'category': 'Purchase Requisition',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_request_for_quotation',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_location.xml',
        'views/admin_purchase_requisition_view.xml',
        'views/rfq_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
