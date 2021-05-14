# -*- coding: utf-8 -*-
{
    'name': "Admin Purchase Order",
    'summary': """
            Purchase Order
        """,
    'author': "Ruel Costob",
    'category': 'Purchase',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_purchase_requisition',
        ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/invoice_delivery.xml',
        'views/admin_po_document_type.xml',
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
