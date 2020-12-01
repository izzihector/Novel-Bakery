# -*- coding: utf-8 -*-

{
    'name': "Customization for payment.",
    'summary': " ",
    'sequence': 0,
    'description': " ",
    'author': "SIT and think digital",
    'website': "",
    'category': 'custom',
    'version': '0.1',
    'depends': [
        'base',
        'account','payment','stock','hr_expense'
    ],
    'data': [
        'security/security.xml',
        'views/cron_view.xml',
        'views/model_view.xml',
    ],
}
