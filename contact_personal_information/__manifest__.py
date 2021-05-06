# -*- coding: utf-8 -*-
{
    "name": "Contact's Personal Information",
    "summary": "Contact's Personal Information",
    "version": "13.0.1",
    "category": "base",
    "author": "Dennis Boy Silva",
    "application": False,
    "installable": True,
    "depends": [
        "partner_firstname",
        "ips_partner_dob"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        'views/scheduler_data.xml',
        "views/partner.xml"
    ],
}
