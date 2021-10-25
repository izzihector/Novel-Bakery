# -*- coding: utf-8 -*-
{
    'name': "POS Analytic Account",
    'summary': """
       Use analytic account defined on POS configuration for POS orders and in Journal Entry""",

    'description': """
        Use analytic account defined on POS configuration for POS orders and in Journal Entry
    """,
    'price': 15.0,
    'currency': 'EUR',
    'author': 'Abdallah Mohamed',
    'license': 'OPL-1',
    'category': 'Point Of Sale, Accounting',
    'website': 'https://www.abdalla.work/r/Ohk',
    'support': 'https://www.abdalla.work/r/Ohk',
    'version': '2.0',
    'depends': ['base', 'point_of_sale', 'account', 'analytic'],
    'data': [
        'views/views.xml',
    ],
    'installable': True,
}
