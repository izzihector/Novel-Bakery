import odoo.addons.decimal_precision as dp
from odoo import _, api, exceptions, fields, models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _name = "purchase.request.line.make.purchase.order"
    _description = "Purchase Request Line Make Purchase Order"

    supplier_id = fields.Many2one('res.partner', string='Supplier',
                                  required=False,
                                  domain=[('supplier', '=', True)])
    item_ids = fields.One2many(
        'purchase.request.line.make.purchase.order.item',
        'wiz_id', string='Items')
    purchase_order_id = fields.Many2one('purchase.order',
                                        string='Purchase Order',
                                        required=False,
                                        domain=[('state', '=', 'draft')])

    @api.model
    def _prepare_item(self, line):
        return {
            'line_id': line.id,
            'request_id': line.request_id.id,
            'product_id': line.product_id.id,
            'name': line.name or line.product_id.name,
            'product_qty': line.product_qty,
            'product_uom_id': line.product_uom_id.id,
        }

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        location = False
        picking_type = False
        company_id = False

        for line in self.env['purchase.request.line'].browse(request_line_ids):

            if line.request_id.state != 'approved':
                raise exceptions.Warning(
                    _('Purchase Request %s is not approved') %
                    line.request_id.name)

            if line.purchase_state == 'done':
                raise exceptions.Warning(
                    _('The purchase has already been completed.'))

            line_company_id = line.company_id \
                              and line.company_id.id or False
            if company_id is not False \
                    and line_company_id != company_id:
                raise exceptions.Warning(
                    _('You have to select lines '
                      'from the same company.'))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise exceptions.Warning(
                    _('You have to enter a Picking Type.'))
            if picking_type is not False \
                    and line_picking_type != picking_type:
                raise exceptions.Warning(
                    _('You have to select lines '
                      'from the same Picking Type.'))
            else:
                picking_type = line_picking_type

    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequestLineMakePurchaseOrder, self).default_get(
            fields)
        request_line_obj = self.env['purchase.request.line']
        request_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not request_line_ids:
            return res
        assert active_model == 'purchase.request.line', \
            'Bad context propagation'

        items = []
        self._check_valid_request_line(request_line_ids)
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines:
            items.append([0, 0, self._prepare_item(line)])
        res['item_ids'] = items
        supplier_ids = request_lines.mapped('supplier_id').ids
        if len(supplier_ids) == 1:
            res['supplier_id'] = supplier_ids[0]
        return res

    @api.model
    def _prepare_purchase_order(self, picking_type, location, company, source):
        if not self.supplier_id:
            raise exceptions.Warning(
                _('Enter a supplier.'))
        supplier = self.supplier_id
        data = {
            'origin': source,
            'partner_id': self.supplier_id.id,
            'fiscal_position_id': supplier.property_account_position_id and
                                  supplier.property_account_position_id.id or False,
            'picking_type_id': picking_type.id,
            'company_id': company.id,
        }
        return data

    @api.model
    def _get_purchase_line_onchange_fields(self):
        return ['product_uom', 'price_unit', 'name',
                'taxes_id']

    @api.model
    def _execute_purchase_line_onchange(self, vals):
        cls = self.env['purchase.order.line']
        onchanges_dict = {
            'onchange_product_id': self._get_purchase_line_onchange_fields(),
        }
        for onchange_method, changed_fields in onchanges_dict.items():
            if any(f not in vals for f in changed_fields):
                obj = cls.new(vals)
                getattr(obj, onchange_method)()
                for field in changed_fields:
                    vals[field] = obj._fields[field].convert_to_write(
                        obj[field], obj)

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        product = item.product_id
        # Keep the standard product UOM for purchase order so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_po_id)
        # Suggest the supplier min qty as it's done in Odoo core
        min_qty = item.line_id._get_supplier_min_qty(product, po.partner_id)
        qty = max(qty, min_qty)
        vals = {
            'name': product.name,
            'order_id': po.id,
            'product_id': product.id,
            'product_uom': product.uom_po_id.id,
            'price_unit': 0.0,
            'product_qty': qty,
            'account_analytic_id': item.line_id.analytic_account_id.id,
            'purchase_request_lines': [(4, item.line_id.id)],
            'date_planned': item.line_id.date_required
        }

        self._execute_purchase_line_onchange(vals)
        return vals

    @api.model
    def _get_purchase_line_name(self, order, line):
        product_lang = line.product_id.with_context({
            'lang': self.supplier_id.lang,
            'partner_id': self.supplier_id.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name

    @api.model
    def _get_order_line_search_domain(self, order, item):
        vals = self._prepare_purchase_order_line(order, item)
        name = self._get_purchase_line_name(order, item)
        order_line_data = [('order_id', '=', order.id),
                           ('name', '=', name),
                           ('product_id', '=', item.product_id.id or False),
                           # ('date_planned', '=', item.line_id.date_required),
                           ('product_uom', '=', vals['product_uom']),
                           ('account_analytic_id', '=',
                            item.line_id.analytic_account_id.id or False),
                           ]
        if not item.product_id:
            order_line_data.append(('name', '=', item.name))
        return order_line_data

    @api.multi
    def make_purchase_order(self):
        res = []
        src_name = []
        purchase_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        pr_line_obj = self.env['purchase.request.line']
        purchase = False

        # for lines in self.item_ids:
        #     src_name.append(lines.request_id.name)
        #     source = str(','.join(map(str, src_name)))
        source = ','.join(self.item_ids.mapped('request_id').mapped('name'))
        # one purchase.order.line may have multiple purchase.request.line
        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise exceptions.Warning(
                    _('Enter a positive quantity.'))

            location = line.request_id.picking_type_id.default_location_dest_id
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(
                    line.request_id.picking_type_id, location,
                    line.company_id, source)

                purchase = purchase_obj.create(po_data)

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
            else:
                po_line_data = self._prepare_purchase_order_line(purchase,
                                                                 item)
                if item.keep_description:
                    po_line_data['name'] = item.name
                po_line = po_line_obj.create(po_line_data)
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line,
                new_pr_line=new_pr_line)
            # po_line.request_id = line.request_id.id
            po_line.origin = source
            po_line.product_qty = new_qty
            po_line._onchange_quantity()
            # The onchange quantity is altering the scheduled date of the PO
            # lines. We do not want that:
            po_line.date_planned = item.line_id.date_required
            res.append(purchase.id)

        return {
            'domain': [('id', 'in', res)],
            'name': _('RFQ'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }


class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _name = "purchase.request.line.make.purchase.order.item"
    _description = "Purchase Request Line Make Purchase Order Item"

    wiz_id = fields.Many2one(
        'purchase.request.line.make.purchase.order',
        string='Wizard', required=True, ondelete='cascade')
    line_id = fields.Many2one('purchase.request.line',
                              string='Purchase Request Line',
                              required=True, )
    request_id = fields.Many2one('purchase.request',
                                 related='line_id.request_id',
                                 string='Purchase Request', )
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(string='Quantity to purchase',
                               digits=dp.get_precision('Product UoS'))
    product_uom_id = fields.Many2one('uom.uom', string='UoM')

    keep_description = fields.Boolean(string='Copy descriptions to new PO',
                                      help='Set true if you want to keep the '
                                           'descriptions provided in the '
                                           'wizard in the new PO.',
                                      default=False)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            code = self.product_id.code
            sup_info_id = self.env['product.supplierinfo'].search([
                '|', ('product_id', '=', self.product_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('name', '=', self.wiz_id.supplier_id.id)])
            if sup_info_id:
                p_code = sup_info_id[0].product_code
                p_name = sup_info_id[0].product_name
                name = '[%s] %s' % (p_code if p_code else code,
                                    p_name if p_name else name)
            else:
                if code:
                    name = '[%s] %s' % (code, name)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1.0
            self.name = name


class PurchaseRequestLineMakePurchaseAgreement(models.TransientModel):
    _name = "purchase.request.line.make.purchase.agreement"
    _description = "Purchase Request Line Make Purchase Agreement"

    purchase_product_ids = fields.One2many(
        'purchase.request.line.make.purchase.agreement.item',
        'agreement_id', string='Request Product')

    @api.model
    def _prepare_item(self, line):
        return {
            'line_id': line.id,
            'request_id': line.request_id.id,
            'product_id': line.product_id.id,
            'name': line.name or line.product_id.name,
            'product_qty': line.product_qty,
            'product_uom_id': line.product_uom_id.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequestLineMakePurchaseAgreement, self).default_get(
            fields)
        request_line_obj = self.env['purchase.request.line']
        request_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not request_line_ids:
            return res
        assert active_model == 'purchase.request.line', \
            'Bad context propagation'

        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines:
            items.append([0, 0, self._prepare_item(line)])
        res['purchase_product_ids'] = items
        return res

    @api.multi
    def make_purchase_agreement(self):

        purchase_agreement = ({'user_id': self.env.uid,
                               'type_id': self.env['purchase.requisition.type'].search([('name', 'like', 'Call')],
                                                                                       limit=1).id,
                               'bid_type': 'single_stage_single_envelope'})

        products = self.env['purchase.request.line.make.purchase.agreement.item'].search(
            [('agreement_id', '=', self.id)])
        agreement_purchase_order = self.env['purchase.requisition'].create(purchase_agreement)
        bool = True
        for rec in products:
            vals = {'requisition_id': agreement_purchase_order.id, 'product_id': rec.product_id.id, 'name': rec.name,
                    'product_qty': rec.product_qty, 'product_uom': rec.product_uom_id.id,
                    'price_unit': rec.product_id.standard_price}
            if len(list(set(products.mapped('product_id')))) == 1 and bool is True:
                club_qty = sum(products.mapped('product_qty'))
                vals.update({'product_qty': club_qty})
                agreement_purchase_order.line_ids.create(vals)
                bool = False
            elif bool is not False:
                agreement_purchase_order.line_ids.create(vals)


class PurchaseRequestLineMakePurchaseAgreementItem(models.TransientModel):
    _name = "purchase.request.line.make.purchase.agreement.item"
    _description = "Purchase Request Line Make Purchase Agreement Item"

    agreement_id = fields.Many2one(
        'purchase.request.line.make.purchase.agreement',
        string='Product', required=True, ondelete='cascade')
    line_id = fields.Many2one('purchase.request.line',
                              string='Purchase Request Line',
                              required=True, )
    request_id = fields.Many2one('purchase.request',
                                 related='line_id.request_id',
                                 string='Purchase Request', )
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(string='Quantity to purchase',
                               digits=dp.get_precision('Product UoS'))
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
