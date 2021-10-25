# -*- coding: utf-8 -*-
{
    'name': "POS Kitchen/Bar Screens",
    'version': '8.0.0.5',
    'category': 'Point of Sale',
    'author': 'SIT & think digital',
    'website': 'http://sitco.odoo.com/',
    'sequence': 0,
    'description': "Each Kitchen/Bar add 1 Display Screen for get requests from Waiters (Customers)"
                   "Kitchen/Chef Session processing products done and change status back Waiters"
                   "Waiters get notifications from event change status of Kitchen/Chef"
                   "And Waiters delivery products Done to Customers",
    'depends': [
        'pos_retail',
        'pos_restaurant',
        'product',
    ],
    'data': [
        'import/template.xml',
        'views/restaurant.xml',
        'views/pos_iot.xml',
        'views/pos_config.xml',
        # 'views/product_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': ['demo/demo.xml'],
    "currency": 'EUR',
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "license": "OPL-1"
}
