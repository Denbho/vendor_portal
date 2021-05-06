# -*- coding: utf-8 -*-

{
    "name" : "Admin App API Connector",
    "author": "Dennis Boy Silva",
    "version" : "13.0.1",
    "summary": 'Used to consume/connect to Outsystem and other external system APIs',
    "description": """Generic SMS Notification""",
    "license" : "OPL-1",
    "depends" : ['base', 'base_setup'],
    "data": [
        'security/ir.model.access.csv',
        'data/api_config_data.xml',
        'views/configuration.xml',
     ],
    "installable": True,
    "auto_install": False,
    "category": "Extra Tools",
}
