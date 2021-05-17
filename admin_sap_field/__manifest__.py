# -*- coding: utf-8 -*-
{
    'name': "Admin SAP Field",
    'summary': """
        SAP field""",
    'author': "Ruel Costob",
    'category': 'tool',
    'version': '13.0.1',
    'depends': [
        'base',
        'account',
        'product',
        'admin_purchase_requisition',
        'admin_purchase_order',
        'admin_contracts_and_agreements',
    ],
    'data': [
        'views/admin_sap_field.xml',
    ],
    'installable': True,
    'auto_install': False,
}
