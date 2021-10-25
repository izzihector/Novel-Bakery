# -*- coding: utf-8 -*-
{
    'name': "HR Attendance Sheet And Policies",
    'summary': """Managing  Attendance Sheets for Employees""",
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.0.2',
    'images': ['static/description/bannar.jpg'],

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_attendance'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/change_att_data_view.xml',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_attendance_policy_view.xml',
        'views/hr_view.xml',
        'views/hr_holidays_view.xml',
        'data/hr_attendance_sheet_data.xml',
    ],

     'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

    'demo': [
        'demo/demo.xml',
    ],
}
