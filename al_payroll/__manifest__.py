# -*- coding: utf-8 -*-
{
    'name': 'Payroll Customization',
    'summary': """Payroll module related customizations""",
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.0.1',

    'depends': ['hr_payroll', 'hr_contract', 'account', 'base', 'hr',
                ],

    'data': ['views/inherited_views.xml',
             'views/deductions_views.xml',
             'security/security.xml',
             'security/ir.model.access.csv',
             'wizard/multi_payslip_confirm.xml',
            ],

    'demo': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
