# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError

class MultiHRPaySlipWiz(models.TransientModel):
    _name = 'multi.hr.payslip.wizard'
    _description = 'Multi HR Pay Slip Wizard'

    @api.multi
    def multi_payslip_hr(self):
        payslip_idsx = self.env['hr.payslip'].browse(self._context.get('active_ids'))
        for payslipx in payslip_idsx:
            if payslipx.state != 'draft':
                raise UserError(_("Selected Payslip(s) cannot be approve by HR as they are not in 'Draft' state."))
            payslipx.action_payslip_hrapproval()
        return {'type': 'ir.actions.act_window_close'}


class MultiFinancePaySlipWiz(models.TransientModel):
    _name = 'multi.finance.payslip.wizard'
    _description = 'Multi Finance Pay Slip Wizard'

    @api.multi
    def multi_payslip_finance(self):
        payslip_idsxx = self.env['hr.payslip'].browse(self._context.get('active_ids'))
        for payslipxx in payslip_idsxx:
            if payslipxx.state != 'hrapproval':
                raise UserError(_("Selected Payslip(s) cannot be approve by Finance as they are not in 'HR Approved' state."))
            payslipxx.action_payslip_finance()
        return {'type': 'ir.actions.act_window_close'}


class MultiPaySlipWiz(models.TransientModel):
    _name = 'multi.payslip.wizard'
    _description = 'Multi Pay Slip Wizard'

    @api.multi
    def multi_payslip(self):
        payslip_ids = self.env['hr.payslip'].browse(self._context.get('active_ids'))
        for payslip in payslip_ids:
            if payslip.state != 'finance':
                raise UserError(_("Selected Payslip(s) cannot be confirmed as they are not in 'Finance Approved' state."))
            payslip.action_payslip_done()
        return {'type': 'ir.actions.act_window_close'}




