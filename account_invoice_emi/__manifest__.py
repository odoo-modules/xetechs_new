# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Invoice EMI',
    'version': '12.0.1',
    'author': 'Laxicon Solution',
    'website': 'http://laxicon.in',
    'category': 'Account',
    'summary': 'Account Invoice EMI',
    'description': '''You can create Invoice EMI.
''',
    'depends': ['sale_management'],
    'data': [
        'data/ir_sequence_data.xml',
        'data/auto_create_invoice.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_emi.xml',
        'views/sales_order.xml',
        'views/partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
