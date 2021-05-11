# -*- coding: utf-8 -*-
{
    'name': "Admin Vendor",
    'summary': """
            Admin Vendor
        """,
    'author': "Ruel Costob",
    'category': 'Base',
    'version': '13.0.1',
    'depends': [
        'purchase',
        'admin_purchase_bid',
        'document_approval',
        'admin_email_notif',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduler_data.xml',
        'wizard/link_vendor_item_to_product.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'auto_install': False,
}
