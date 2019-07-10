# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Issue',
    'version': '12.0',
    'category': 'Project',
    'sequence': 40,
    'summary': 'Project Issue',
    'description': """
Issues for Projects
    """,
    'website': 'https://www.odoo.com/page/project-management',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/project_issue_views.xml',
        'views/project_project_view.xml',
        'views/project_task_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
