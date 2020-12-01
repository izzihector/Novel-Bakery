
from odoo import models, fields, api, SUPERUSER_ID, _
from werkzeug import url_encode
from odoo.tools import email_split, float_is_zero
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class InheritExpenses(models.Model):
    _inherit = 'hr.expense'

    have_bank_fees = fields.Selection([('nf','No Fees'),('wf','With Fees')],default='nf')
    bank_fees = fields.Float('Bank Fees')
    bank_fees_account = fields.Many2one('account.account')
    vat_fees = fields.Float('VAT Amount')
    vat_fees_account = fields.Many2one('account.account')
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='company_account', states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")

    @api.multi
    def action_submit_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else '',
                'default_bank_fees': self.bank_fees,
                'default_vat_fees':self.vat_fees,
                'default_bank_fees_account':self.bank_fees_account.id,
                'default_vat_fees_account':self.vat_fees_account.id,
                'default_have_bank_fees':self.have_bank_fees,
            }
        }

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.currency_id and expense.currency_id != company_currency

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.employee_id.address_home_id.commercial_partner_id.id

            # source move line
            amount = taxes['total_excluded']
            amount_currency = False
            if different_currency:
                amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'partner_id': partner_id,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'currency_id': expense.currency_id.id if different_currency else False,
            }
            move_line_values.append(move_line_src)
            total_amount += -move_line_src['debit'] or move_line_src['credit']
            total_amount_currency += -move_line_src['amount_currency'] if move_line_src['currency_id'] else (-move_line_src['debit'] or move_line_src['credit'])

            # taxes move lines
            for tax in taxes['taxes']:
                amount = tax['amount']
                amount_currency = False
                if different_currency:
                    amount = expense.currency_id._convert(amount, company_currency, expense.company_id, account_date)
                    amount_currency = tax['amount']
                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                    'amount_currency': amount_currency if different_currency else 0.0,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_line_id': tax['id'],
                    'expense_id': expense.id,
                    'partner_id': partner_id,
                    'currency_id': expense.currency_id.id if different_currency else False,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                }
                total_amount -= amount
                total_amount_currency -= move_line_tax_values['amount_currency'] or amount
                move_line_values.append(move_line_tax_values)

            # bank fees move line
            move_line_bank_fees = {
                'name': move_line_name,
                'debit': self.bank_fees,
                'credit': 0,
                'account_id': self.bank_fees_account.id,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            if self.have_bank_fees == 'wf':
                move_line_values.append(move_line_bank_fees)

            # vat fees move line
            move_line_vat_fees = {
                'name': move_line_name,
                'debit': self.vat_fees,
                'credit': 0,
                'account_id': self.vat_fees_account.id,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            if self.have_bank_fees == 'wf':
                move_line_values.append(move_line_vat_fees)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount + self.bank_fees + self.vat_fees,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.currency_id.id if different_currency else False,
                'expense_id': expense.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)


            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense


class InheritExpensesSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    bank_fees = fields.Float('Bank Fees')
    bank_fees_account = fields.Many2one('account.account')
    vat_fees = fields.Float('VAT Amount')
    vat_fees_account = fields.Many2one('account.account')
    have_bank_fees = fields.Selection([('nf', 'No Fees'), ('wf', 'With Fees')])
    total_without_bank_fees = fields.Float()
    is_post_bank = fields.Boolean(default=False)
    have_je = fields.Boolean(default=False)

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(
                    r.currency_id or self.env.user.company_id.currency_id).rounding))
        if self.have_bank_fees == 'wf':
            self.is_post_bank = True

        res = expense_line_ids.action_move_create()
        self.account_move_id.bank_je_id = self.id
        self.have_je = True

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res


    # @api.multi
    # def create_expense_bank_je(self):
    #     sequence_code = self.journal_id.sequence_id.code
    #     bank_moves = self.env['account.move'].create({
    #                         'name': self.env['ir.sequence'].next_by_code(sequence_code),
    #                         'ref': 'Bank Fees'+':'+self.name,
    #                         'journal_id': self.journal_id.id,
    #                         'bank_je_id': self.id,
    #                         'partner_id':self.env['res.partner'].search([('name','=',self.employee_id.name)], limit=1).id,
    #                         'date': self.accounting_date,
    #                         'line_ids': [
    #                             (0, 0, {
    #                                 'name': 'Bank Fees'+':'+self.name,
    #                                 'debit': self.bank_fees,
    #                                 'account_id': self.bank_fees_account.id,
    #                                 'partner_id': self.env['res.partner'].search([('name','=',self.employee_id.name)], limit=1).id,
    #                                 'date': self.accounting_date,
    #                                 'date_maturity':self.accounting_date,
    #                             }),
    #                             (0, 0, {
    #                                 'name': 'Bank Fees tax'+':'+self.name,
    #                                 'debit': self.vat_fees,
    #                                 'account_id': self.vat_fees_account.id,
    #                                 'partner_id': self.env['res.partner'].search([('name','=',self.employee_id.name)], limit=1).id,
    #                                 'date': self.accounting_date,
    #                                 'date_maturity': self.accounting_date,
    #
    #                             }),
    #                             (0, 0, {
    #                                 'name': 'Bank Charges',
    #                                 'credit': self.vat_fees+self.bank_fees,
    #                                 'account_id': self.bank_fees_account.id,
    #                                 'partner_id': self.env['res.partner'].search([('name','=',self.employee_id.name)], limit=1).id,
    #                                 'date': self.accounting_date,
    #                                 'date_maturity': self.accounting_date,
    #
    #                             }),
    #                         ]
    #                     })
    #     self.is_post_bank = False
    #     bank_moves.post()

    @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('bank_je_id', 'in', self.ids)],
            }

class InheritMoveLine(models.Model):
    _inherit = 'account.move'
    bank_je_id = fields.Integer()

class InheritExpensePaymentWizard(models.TransientModel):
    _inherit = 'hr.expense.sheet.register.payment.wizard'

    have_bank_fees = fields.Selection([('nf','No Fees'),('wf','With Fees')],default='wf')
    bank_fees = fields.Float('Bank Fees')
    bank_fees_account = fields.Many2one('account.account')
    vat_fees = fields.Float('VAT Amount')
    vat_fees_account = fields.Many2one('account.account')


    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'have_bank_fees': 'wf' if self.have_bank_fees == 'wf' else 'nf',
            'bank_fees': self.bank_fees,
            'bank_fees_account': self.bank_fees_account.id,
            'vat_fees': self.vat_fees,
            'vat_fees_account': self.vat_fees_account.id,
            'has_bank_payment': False if self.have_bank_fees == 'wf' else True,
            'bank_fees_id': True if self.have_bank_fees == 'wf' else False,
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'has_expense_bank_payment': True,
            'partner_id': self.partner_id.id,
            'partner_bank_account_id': self.partner_bank_account_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication
        }

    @api.multi
    def expense_post_payment(self):
        self.ensure_one()
        self.create_je_register_payment()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()

        # Log the payment in the chatter
        body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
        expense_sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

        return {'type': 'ir.actions.act_window_close'}

    def create_je_register_payment(self):
        if self.have_bank_fees == 'wf':
            sequence_code = self.journal_id.sequence_id.code
            bank_moves = self.env['account.move'].create({
                            'name': self.env['ir.sequence'].next_by_code(sequence_code),
                            'ref': self.communication,
                            'journal_id': self.journal_id.id,
                            'date': self.payment_date,
                            'line_ids': [
                                (0, 0, {
                                    'name': 'Bank Fees',
                                    'debit': self.bank_fees,
                                    'account_id': self.bank_fees_account.id,
                                    'partner_id': self.partner_id.id,
                                    'date': self.payment_date,
                                    'date_maturity': self.payment_date
                                }),
                                (0, 0, {
                                    'name': 'Bank Fees tax',
                                    'debit': self.vat_fees,
                                    'account_id': self.vat_fees_account.id,
                                    'partner_id': self.partner_id.id,
                                    'date': self.payment_date,
                                    'date_maturity': self.payment_date
                                }),
                                (0, 0, {
                                    'name': 'Bank Charges',
                                    'credit': self.vat_fees + self.bank_fees,
                                    'account_id': self.bank_fees_account.id,
                                    'partner_id': self.partner_id.id,
                                    'date': self.payment_date,
                                    'date_maturity': self.payment_date
                                }),
                            ]
                        })
            bank_moves.post()
