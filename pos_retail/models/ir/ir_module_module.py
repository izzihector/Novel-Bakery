# -*- coding: utf-8 -*-
from odoo import api, models, fields

class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    def button_immediate_upgrade(self):
        self.env.cr.execute("delete from ir_model_relation where name='account_tax_sale_order_line_insert_rel'")
        self.env.cr.commit()
        res = super(IrModuleModule, self).button_immediate_upgrade()
        self.env['pos.call.log'].sudo().search([]).unlink()
        self.env['pos.cache.database'].sudo().search([]).unlink()
        return res
