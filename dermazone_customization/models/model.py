from odoo import api, fields, models, _

class InheritSaleOrderLines(models.Model):
    _inherit = "sale.order.line"

    lot_number = fields.Many2one('stock.production.lot')
    expiry_date = fields.Datetime(related='lot_number.use_date')

    @api.onchange('product_id')
    def change_lot_number(self):
        lot_list = []
        if self.product_id:
            lots = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
            for rec in lots:
                lot_list.append(rec.id)
        return {'domain': {'lot_number': [('id', 'in',lot_list)]}}


class InheritInvoiceLines(models.Model):
    _inherit = 'account.invoice.line'

    lot_number = fields.Many2one('stock.production.lot')
    expire_date = fields.Datetime(related='lot_number.use_date')

    @api.onchange('product_id')
    def change_lot_number(self):
        lot_list = []
        if self.product_id:
            lots = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
            for rec in lots:
                lot_list.append(rec.id)
        return {'domain': {'lot_number': [('id', 'in',lot_list)]}}



