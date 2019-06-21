# -*- coding: utf-8 -*-
{
    'name': 'Dynamic List View',
    'summary': 'Customize list views on the fly with Switch mode and Export Listview.',
    'version': '12.0.2.0',
    'description': """Customize list views on the fly with Switch mode and Export Listview.""",
    'catagory': 'Tools',
    'author': "Crest Infosys",
    'license': 'OPL-1',
    'depends': ['web', 'web_export_list_xls'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/assets_registary.xml',
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
    'images': ['static/description/main_screenshot.png'],
    'price': 119.0,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
