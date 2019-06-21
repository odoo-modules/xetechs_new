# -*- coding: utf-8 -*-
{
    "name": "Web Export ListView XLS", 
    'category': 'Extra Tools',
    "summary": "Dynamic Listview Export Button",
    "description": """This module enables the feature to Listview export in xls""",
    'version': '12.0.1.0',
    'author': "Crest Infosys",
    'license': 'OPL-1',
    'depends': ['web'],
    "data": [
        'security/web_export_security.xml',
        'views/web_export_template.xml',
    ],
    'qweb': [
        "static/src/xml/web_export_list_xls.xml",
    ],
    # 'images': ['static/description/main_screenshot.png'],
    'price': 5.0,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False
}