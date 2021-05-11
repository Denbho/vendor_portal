# -*- coding: utf-8 -*-
{
    'name': "Vendor Request For Product Proposal",
    'summary': """
        Vendor Request For Product Proposal Management""",
    'description': """
    """,
    'author': "Dennis Boy Silva",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'document_approval',
        'admin_purchase_requisition'
        ],
    'data': [
        'wizard/link_rfq_item_to_product_view.xml',
        'views/request_for_proposal.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'installable': True,
    'auto_install': False,
}
