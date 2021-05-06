# -*- coding: utf-8 -*-
{
    'name': "Birthday Wishes to Partner",

    'summary': """
     Send Birthday Email wishes to your partners by adding date of births on their profiles""",

    'description': """
    Send Birthday Email wishes to your partners by adding date of births on their profiles

    1. Group and Filter your partner using thier day of birth
    2. Define Birthday Email templates and assign to your partners. Rich Text and Images are supported on Email templates 
    3. Switch On Automatic Birthday Email for some partners and switch off for someone else.

    """,

    'author': "IctPack Solutions LTD",
    'website': 'https://www.ictpack.com',
    'support': 'projects@ictpack.com',
    'category': 'Tools',
    'version': '13.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['mail'],

    # always loaded
    'data': [
        'data/scheduler_data.xml',
        'data/mail_template_data.xml',
        'views/res_partner_views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 10,
    'currency': 'EUR',
    'license': 'OPL-1',

    'images':[
        'static/description/banner.gif'
    ],
}
