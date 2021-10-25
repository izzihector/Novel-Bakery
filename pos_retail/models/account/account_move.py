# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):

    _inherit = "account.move"

    @api.model
    def create(self, vals):
        move = super(AccountMove, self).create(vals)
        return move

    @api.multi
    def post(self, invoice=False):
        self._post_validate()
        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date, move_id=move.id).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        return self.write({'state': 'posted'})

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    def _prepare_analytic_line(self):
        analytic_line_value = super(AccountMoveLine, self)._prepare_analytic_line()
        if analytic_line_value and analytic_line_value[0] and not analytic_line_value[0].get('name', None):
            analytic_line_value[0]['name'] = self.ref or self.move_id.ref
        return analytic_line_value[0]
