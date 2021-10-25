# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class pos_sale_report_template(models.AbstractModel):
    _name = 'report.pos_retail.pos_sale_report_template'
    _description = "Template Report of sale"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('pos_retail.pos_sale_report_template')
        if data and data.get('form') and data.get('form').get('session_ids'):
            docids = self.env['pos.session'].browse(data['form']['session_ids'])
        return {'doc_ids': self.env['pos.sale.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_ids']),
                'data': data,
                }

class pos_sale_transaction_report_template(models.AbstractModel):
    _name = 'report.pos_retail.pos_sale_transaction_report_template'
    _description = "Template Report of sale"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('pos_retail.pos_sale_transaction_report_template')
        if data and data.get('form') and data.get('form').get('session_transaction_id'):
            docids = self.env['pos.session'].browse(data['form']['session_transaction_id'])
        return {'doc_ids': self.env['pos.sale.transaction.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_transaction_id']),
                'data': data,
                }


class pos_sale_report(models.TransientModel):
    _name = 'pos.sale.report'
    _description = "Report of sale"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('pos_retail.pos_sale_report_template')
        if data and data.get('form') and data.get('form').get('session_ids'):
            docids = self.env['pos.session'].browse(data['form']['session_ids'])
        return {'doc_ids': self.env['pos.sale.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_ids']),
                'data': data,
                }

    @api.multi
    def print_receipt(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'pos.sale.report'
                }
        return self.env.ref('pos_retail.report_pos_sales_pdf').report_action(self, data=datas)

    session_ids = fields.Many2many('pos.session', 'pos_sale_report_session_rel', 'wizard_id', 'session_id', string="Closed Session(s)")
    report_type = fields.Selection([('thermal', 'Thermal'),
                                    ('pdf', 'PDF')], default='pdf', readonly=True, string="Report Type")


class pos_transaction_report(models.TransientModel):
    _name = 'pos.sale.transaction.report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('pos_retail.pos_sale_transaction_report_template')
        if data and data.get('form') and data.get('form').get('session_transaction_id'):
            docids = self.env['pos.session'].browse(data['form']['session_transaction_id'])
        return {'doc_ids': self.env['pos.sale.transaction.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['pos.session'].browse(data['form']['session_transaction_id']),
                'data': data,
                }

    @api.multi
    def print_transaction(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'pos.sale.transaction.report'
                }
        return self.env.ref('pos_retail.report_pos_sales_transaction_pdf').report_action(self, data=datas)

    session_transaction_id = fields.Many2many('pos.session', 'pos_sale_transaction_rel', 'session_id','transaction_id', string='Sessions(s)')
    report_type = fields.Selection([('thermal', 'Thermal'),
                                    ('pdf', 'PDF')], default='pdf', readonly=True, string="Report Type")