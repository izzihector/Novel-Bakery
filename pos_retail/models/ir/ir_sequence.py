# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
import logging

_logger = logging.getLogger(__name__)

class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    def _next(self):
        """
        Issue: psycopg2.OperationalError: could not obtain lock on row in relation "ir_sequence_date_range"
        Comming from :  "/home/odoo/src/odoo/odoo/addons/base/models/ir_sequence.py", line 52, in _update_nogap
        self._cr.execute("SELECT number_next FROM %s WHERE id=%s FOR UPDATE NOWAIT" % (self._table, self.id))
        (***)
        ================
        Solution:
        if def post of account move, save move_id to context
        We return back move_id of this method
        No need call method _update_nogap, if call it will have issue (***)
        """
        context = self.env.context
        move_id = context.get('move_id', None)
        if move_id:
            _logger.info('==> force move_id %s become end of sequence number' % move_id)
            return self.sequence_id.get_next_char(move_id)
        else:
            return super(IrSequenceDateRange, self)._next()


class ir_sequence(models.Model):
    _inherit = "ir.sequence"

    def _next(self):
        context = self.env.context
        move_id = context.get('move_id', None)
        number = super(ir_sequence, self)._next()
        return number
