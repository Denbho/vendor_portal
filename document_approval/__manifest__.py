# -*- coding: utf-8 -*-
{
    'name': "Default Approvals",
    'summary': "3levels of approvals",
    'description': """
        Submit -> Confirm -> Verify - Approve
        Cancel -> Reset to draft

        Use the following buttons name:
            * submit_request
            * confim_request
            * verify_request
            * approve_request
            * cancel_request
            * reset_to_draft_request
    """,
    'author': "Dennis Boy Silva - Agilis Enterprise Solutions, Inc.",
    'website': "http://www.agilis.com.ph",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Training Material',
    'version': '12.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.cs
        # 'views/sales.xml'
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    'auto_install': False,
}
