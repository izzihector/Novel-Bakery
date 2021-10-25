# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)

class RestaurantPrinter(models.Model):
    _inherit = "restaurant.printer"

    print_type = fields.Selection([
        ('posbox', 'PosBox'),
        ('network', 'Lan Network')
    ], default='posbox', string='Print type', required=1)
    printer_id = fields.Many2one('pos.epson', 'Epson Printer Network Device')
    branch_id = fields.Many2one(
        'pos.branch',
        'Branch',
        help='Only Branch Assigned can use this printer'
    )