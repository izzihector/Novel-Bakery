# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Odoo import for BOM using csv / xlsx',
    'version' : '1.0',
    'author' : 'Globalteckz',
    'category' : 'Extra Tools',
	"price": "15.00",
    "currency": "EUR",
    'license': 'Other proprietary',
    "summary":"This Module can be used to import your BOM via csv and xls",
    'website': 'https://www.globalteckz.com',
    'images': ['static/description/Banner.png'],
    'description' : """
Import BOM
excel bom
Import excel bom
xls bom
Import xls bom
csv bom
Import csv bom
import Bill of material
import bill of material
import excel bill of material
xls bill of material
import csv bill of material
import xls bill of material
with different scenario as per your business requirements
""",
    "summary":"This Module can be used to import your BOM",
    'depends' : ['base','mrp','account','l10n_us'],
    'data': [
        'view/bom_wizard.xml',
    ],
    'qweb' : [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
