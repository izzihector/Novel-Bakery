# -*- coding: utf-8 -*-
{
    'name': "POS Local Network",
    'version': '1.0.4',
    'category': 'Point of Sale',
    'description': "Odoo POS Original, each Printer Kitchen required one posbox/iot box \n"
                   "Odoo POS Original not support print viva Lan Network \n"
                   "This Module supported print viva Lan Network Printers with only one posbox/iot box \n",
    'author': 'SIT & think digital',
    'website': 'http://sitco.odoo.com',
    'sequence': 0,
    'depends': [
        'pos_retail',
        'pos_restaurant'
    ],
    'demo': [

    ],
    'data': [
        'security/ir.model.access.csv',
        'template/import_library.xml',
        'views/pos_config.xml',
        'views/pos_epson.xml',
        'views/restaurant_printer.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    "currency": 'EUR',
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "license": "OPL-1",
    'installable': True,
    'application': True,
    'post_init_hook': 'auto_action_after_install',
}
