from odoo import api, fields, models, _
from datetime import timedelta
import datetime

class InheritSaleOrders(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _action_confirm(self):
        for rec in self.picking_ids[0]:
            for record in rec.move_ids_without_package:
                for line in self.order_line:
                    if record.product_id == line.product_id:
                        record.product_uom_qty = line.product_uom_qty + line.bonus_qty
        res = super(InheritSaleOrders,self)._action_confirm()
        return res

    def get_customer_value(self):
        date_before_six_months = datetime.datetime.now() - timedelta(days=182)
        last_payment = self.env['account.payment'].search([('partner_id', '=', self.partner_id.id),('state', '=', 'posted')],order='payment_date desc', limit=1)
        last_payment_date = last_payment.payment_date
        last_payment_value = last_payment.amount
        payment_record = self.env['account.payment'].search([('partner_id','=',self.partner_id.id),('payment_date','>=',date_before_six_months),('state','=','posted')])
        total_payment = 0
        for record in payment_record:
            total_payment += record.amount

        total_sale = 0
        for rec in self:
            if rec.confirmation_date:
                if rec.confirmation_date >= date_before_six_months:
                    total_sale += rec.amount_total
        return total_sale, total_payment, last_payment_date, last_payment_value

    def get_invoice_value(self):
        date_before_one_months = datetime.datetime.now() - timedelta(days=30)
        date_before_twelve_months = datetime.datetime.now() - timedelta(days=365)
        last_invoice = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id),('state', '!=', 'cancel')], order='date_invoice desc', limit=1).date_invoice
        invoice_record_twelve = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),('date_invoice','>=',date_before_twelve_months),('state','!=','cancel')])
        invoice_record_one = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id), ('date_invoice', '>=', date_before_twelve_months),
             ('state', '!=', 'cancel')])
        total_inv_one_months = 0
        for records in invoice_record_one:
            total_inv_one_months += records.amount_total
        total_inv_twelve_months = 0
        for records in invoice_record_twelve:
            total_inv_twelve_months += records.amount_total
        return total_inv_twelve_months, last_invoice, total_inv_one_months

class InheritPartner(models.Model):
    _inherit = 'res.partner'

    english_name = fields.Char(required=False)