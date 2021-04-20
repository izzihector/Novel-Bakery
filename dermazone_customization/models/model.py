from odoo import api, fields, models, _
from odoo.exceptions import UserError

class InheritSaleOrder(models.Model):
    _inherit = "sale.order"

    sale_representative = fields.Many2one('res.users', 'Sales Representative', ondelete='restrict', required=True)

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'sale_representative': self.sale_representative.id,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        }
        return invoice_vals


class InheritSaleOrderLines(models.Model):
    _inherit = "sale.order.line"

    lot_number = fields.Many2one('stock.production.lot', change_default=True, ondelete='restrict')
    expiry_date = fields.Datetime(related='lot_number.use_date')
    bonus_qty = fields.Float()
    sale_representative_id = fields.Many2one(related='order_id.sale_representative', store=True, string='Sales Representative', readonly=True)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        super(InheritSaleOrderLines, self).product_id_change()
        self.lot_number = False

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        product = self.product_id.with_context(force_company=self.company_id.id)
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'lot_number': self.lot_number.id,
            'expire_date': self.expiry_date,
            'quantity': qty,
            'discount': self.discount,
            'bonus_qty': self.bonus_qty,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
        }
        return res

    @api.onchange('product_id')
    def change_lot_number(self):
        lot_list = []
        if self.product_id:
            lots = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)])
            for rec in lots:
                lot_list.append(rec.id)
        return {'domain': {'lot_number': [('id', 'in',lot_list)]}}

class InheritAccountInvoice(models.Model):
    _inherit = "account.invoice"

    sale_representative = fields.Many2one('res.users', 'Sales Representative', ondelete='restrict')


class InheritInvoiceLines(models.Model):
    _inherit = 'account.invoice.line'

    lot_number = fields.Many2one('stock.production.lot', change_default=True, ondelete='restrict')
    expire_date = fields.Datetime(related='lot_number.use_date')
    bonus_qty = fields.Float()

    @api.onchange('product_id')
    def change_lot_number(self):
        lot_list = []
        if self.product_id:
            lots = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id),('product_qty','>',0)])
            for rec in lots:
                lot_list.append(rec.id)
        return {'domain': {'lot_number': [('id', 'in',lot_list)]}}


class StockLotProduction(models.Model):
    _inherit = 'stock.production.lot'

    production_date = fields.Datetime('Production Date')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.name and record.use_date and record.product_qty:
                name = str(record.name)+" [Exp("+str(record.use_date)+ "),Stock("+str(record.product_qty)+" "+str(record.product_uom_id.name)+")]"
            else:
                record.name = name
            result.append((record.id, name))
        return result
