# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Dermazone Customizations.',
    'version': '1.1',
    'summary': 'Customized module for all the general requirements of dermazone project',
    'sequence': 3,
    'author': "SIT & Think Digital",
    'website': "sitco.odoo.com",
    'description': "",
    'depends': ['base','sale','account','product_expiry'
    ],
    'data': [
        'views/views.xml',
        'views/reports.xml',
        'reports/evaluation_report.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
