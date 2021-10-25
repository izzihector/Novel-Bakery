# -*- coding: utf-8 -*-

{
    'name': 'HRMS Resignation',
    'summary': 'Handle the resignation process of the employee',
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.0.2',
    'depends': ['mail','hr','al_payroll'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/resign_employee.xml',
        'views/hr_employee.xml',
        'views/resignation_view.xml',
        'views/approved_resignation.xml',
        'views/resignation_sequence.xml',
            ],

    'demo': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

