# -*- coding: utf-8 -*-
{
    'name': 'Dashboard Custom Reports',
    'summary': """All Dashboard Custom reports for Management""",
    'author': "SIT & think digital",
    'website': "http://sitco.odoo.com/",
    'category': 'Custom',
    'version': '12.1.2',

    'depends': ['purchase','sale','account','point_of_sale'],

    'data': ['security/security.xml',
             'views/inherited_views.xml'],

    'demo': [],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
