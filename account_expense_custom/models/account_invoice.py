# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            if invoice.invoice_line_ids.expense_nature == 'prepaid':
                vals = {
                    'date': fields.Date.today(),
                    'journal_id': invoice.journal_id.id,
                    'amortization_method': 'monthly',
                    'reference': invoice.number,
                    'payment_type': 'credit',
                    'vendor_id': invoice.partner_id.id,
                    'invoice_id': invoice.id,
                    'move_id': invoice.move_id.id
                }
                transaction_rec = self.env['account.expense.transaction'].create(vals)

                for invoice_line in invoice.invoice_line_ids:
                    line_vals = {
                        'expense_transaction_id': transaction_rec.id,
                        'expense_type_id': invoice_line.expense_type_id.id,
                        'description': invoice_line.name,
                        'prepaid_expense_account_id': invoice_line.expense_type_id.prepaid_expense_account_id.id,
                        'expense_account_id': invoice_line.expense_type_id.expense_account_id.id,
                        'analytic_account_id': invoice_line.account_analytic_id.id,
                        'analytic_tag_ids': invoice_line.analytic_tag_ids and [(6, 0, invoice_line.analytic_tag_ids.ids)],
                        'start_date': invoice_line.start_date,
                        'end_date': invoice_line.end_date,
                        'quantity': invoice_line.quantity,
                        'price_unit': invoice_line.price_unit
                    }
                    self.env['expense.detail.line'].create(line_vals)
            return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    expense_nature = fields.Selection([('normal', 'Normal'), ('prepaid', 'Prepaid')],
                                      string='Type Bills', required=True,
                                      default="normal")

    expense_type_id = fields.Many2one("account.expense.type",
                                             string="Expense Type",
                                             domain=[('state', '=', 'confirmed')])
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.onchange('expense_nature')
    def onchange_expense_nature(self):
        if self.expense_nature != 'prepaid':
            for invoice_line in self:
                invoice_line.end_date = False
                invoice_line.start_date = False
                invoice_line.expense_type_id = False
        if self.expense_nature == 'prepaid':
            for invoice_line in self:
                invoice_line.account_id = invoice_line.product_id.expense_type_id.prepaid_expense_account_id.id


    @api.onchange('product_id')
    def onchange_product_id_expense(self):
        if self.product_id and self.expense_nature == 'prepaid':
            self.expense_type_id = self.product_id.expense_type_id.id
