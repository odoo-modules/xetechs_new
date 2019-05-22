# -*- coding: utf-8 -*-
{
    'name': "Project Task Start Stop and Pause",
    'version': "1.1.6",
    'author': 'AppsTG',
    'website': 'https://appstg.com',
    'support': "info@appstg.com",
    'category': "Project",
    'summary': "Add Start, Stop and Pause buttons in Kanban and Form view with the preservation of working time in the timesheets",
    'description': "",
    'license':'OPL-1',
    'price': 24.90,
    'currency': 'EUR',
    'images':['static/description/banner.jpg'],
    'data': [
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'depends': ['project', 'hr_timesheet', 'bus'],
    'application': True,
}
