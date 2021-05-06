# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Product Information",
    'summary': """
        Vendor Request For Product Information Management""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'document_approval',
        'admin_purchase_requisition',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/request_for_information.xml'
    ],
    'installable': True,
    'auto_install': False,
}
