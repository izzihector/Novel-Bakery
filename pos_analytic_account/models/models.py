# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )


class PosOrder(models.Model):
    _inherit = 'pos.order'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        related="session_id.config_id.account_analytic_id",
        copy=False, store=True, string='Analytic Account')

    @api.model
    def _prepare_analytic_account(self, line):
        return line.order_id.session_id.config_id.account_analytic_id.id

    # FIXME: easiest way to solve it by contribute to Odoo SA and solve it in source code
    def _prepare_account_move_and_lines(self, session=None, move=None):
        """
        Override function
        to add analytic account for COGS and Stock Interim Account (Delivered)
        account based on company configuration.
        :param session: pos session
        :param move: account move if it created
        :return: account move lines values
        """
        res = super(PosOrder, self)._prepare_account_move_and_lines(session,
                                                                    move)
        for order in self:
            if order.company_id.anglo_saxon_accounting:
                grouped_data = res["grouped_data"]
                for group_key, group_data in grouped_data.items():
                    if group_key[0] == "counter_part":
                        # try to find additional move lines vals
                        for value in group_data:
                            if value["name"] != _("Trade Receivables"):
                                # need to get move line that contain COGS or Interim
                                value.update({
                                    "analytic_account_id": order.account_analytic_id.id or False,
                                })
        return res


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        related="order_id.session_id.config_id.account_analytic_id",
        store=True, string='Analytic Account', copy=False
    )


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.one
    def action_pos_session_closing_control(self):
        ctx = dict(self._context, add_analytic_account_id=self.config_id.account_analytic_id.id)
        return super(PosSession, self.with_context(ctx)).action_pos_session_closing_control()


    @api.one
    def action_pos_session_validate(self):
        ctx = dict(self._context, add_analytic_account_id=self.config_id.account_analytic_id.id)
        return super(PosSession, self.with_context(ctx)).action_pos_session_validate()

class AML(models.Model):
    _inherit = "account.move.line"

    @api.model
    def create(self, vals_list):
        analytic_account_id = self._context.get('add_analytic_account_id', False)
        if analytic_account_id:
            vals_list['analytic_account_id'] = analytic_account_id
        return super(AML, self).create(vals_list)
