# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    printer_id = fields.Many2one(
        'pos.epson',
        'Printer Network',
        help='If you choice printer here, bill/receipt of pos order will print direct to this printer\n'
             'And not print at printer direct usb posbox'
    )