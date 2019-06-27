# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################


{
    'name': 'Sales Commission With Target (Enterprise)',
    'summary': 'Commission to Sales Person, Consultant, Distributor',
    'version': '1.0',
    'description': """Sales Commission with Target.""",
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Sales',
    'website': "http://www.acespritech.com",
    'price': 60.00,
    'currency': 'EUR',
    'depends': ['base', 'account', 'sale_management', 'hr_payroll'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_invoice_scheduler.xml',
        'views/sale_team_view.xml',
        'views/sales_commission.xml',
        'views/sales_commission_calculation_details_view.xml',
        'views/sale_view.xml',
        'views/product_view.xml',
        'views/hr_payroll_view.xml',
        'views/hr_payroll_data.xml',
        'views/account_view.xml',
        'views/sales_configuration_view.xml',
        'views/consultant_configuration_view.xml',
        'views/distributor_configuration_view.xml',
        'views/commission_allocate_rate.xml',
        'views/sales_target_view.xml',
        'report/print_commission_template.xml',
        'report/report.xml',
        'views/commission_summary_email_template.xml',
        'wizard/sales_commission_payment_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
