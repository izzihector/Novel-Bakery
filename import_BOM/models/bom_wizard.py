# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
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

from openerp import fields, models ,api, _
from tempfile import TemporaryFile
from openerp.exceptions import UserError, ValidationError
from datetime import  datetime
from odoo.exceptions import UserError
from odoo import api, exceptions, fields, models, _
#from datetime import  timedelta

import base64
import copy
import datetime
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import date
from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
import xlrd
import collections
from collections import Counter
from xlrd import open_workbook
import csv
import base64
import sys
from odoo.tools import pycompat
import datetime
import calendar



class Bom_wizard(models.TransientModel):
    _name = 'bom.wizard'


    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    bom_type = fields.Selection([('mp', 'Manufacture Product'), ('kit', 'Kit')], string='Bom Type')



    @api.multi
    def Import_BOM(self):
        product_tem_obj = self.env['product.template']
        product_obj = self.env['product.product']

        mrp_result = {}
        mrp_obj = self.env['mrp.bom']
        mrp_obj_fileds = mrp_obj.fields_get()
        mrp_default_value = mrp_obj.default_get(mrp_obj_fileds)
        mrp_line_obj = self.env['mrp.bom.line']
        line_fields = mrp_line_obj.fields_get()
        file_data = False
        if self.select_file and self.data_file and self.bom_type:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or bom type'))

        for row in file_data:
            product_tem = product_tem_obj.search([('name', '=', row[0]),('default_code', '=', row[1])])
            product_rows = product_obj.search([('name', '=', row[3])])
            if not product_tem:
                raise ValidationError("Product  '%s' not found"%row[0])
            if not product_rows:
                raise ValidationError("Product  '%s' not found"%row[3])

            mrp_obj_update = mrp_default_value.copy()
            mrp_obj_update.update({
                'product_tmpl_id': product_tem.id,
                'product_qty': row[2],
                'product_uom_id': product_tem.uom_id.id,
                'type': self.bom_type == 'mp' and 'normal' or 'phantom',
                'code': row[1],

            })
            line_v1 = mrp_line_obj.default_get(line_fields)
            line_vals = line_v1.copy()
            line_vals.update({'product_id': product_rows.id, 'product_qty': row[4] and int(row[4]) or 1,
                          'product_uom_id': product_rows.uom_id.id})
            l2 = [(0, 0, line_vals)]
            if mrp_result.get(row[0]):
                l1 = mrp_result[row[0]]['bom_line_ids']
                mrp_result[row[0]].update({'bom_line_ids': l1 + l2})
            if not mrp_result.get(row[0]):
                mrp_obj_update.update({'bom_line_ids': l2})
                mrp_result[row[0]] = mrp_obj_update
        for mrp_data in mrp_result.values():
            mrp_gen = mrp_obj.create(mrp_data)
            print ("::::::::::::::::::mrp_gen::::::::::::::::",mrp_gen)
        return True

