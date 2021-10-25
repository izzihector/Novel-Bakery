odoo.define('pos_retail.sync_stock', function (require) {
    var models = require('point_of_sale.models');
    var rpc = require('pos.rpc');

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _do_update_quantity_onhand: function (product_ids) {
            var self = this;
            var stock_location_ids = this.get_locations();
            if (stock_location_ids.length == 0 || !stock_location_ids) {
                return
            }
            return this._get_stock_on_hand_by_location_ids(product_ids, stock_location_ids).done(function (datas) {
                var products = [];
                for (var product_id in datas) {
                    var product = self.db.product_by_id[product_id];
                    if (product) {
                        products.push(product);
                        var qty_available = datas[product_id];
                        self.db.stock_datas[product['id']] = qty_available;
                        console.log('-> ' + product['display_name'] + ' qty_available : ' + qty_available)
                    }
                }
                if (products.length) {
                    self.gui.screen_instances["products"].do_update_products_cache(products);
                    self.gui.screen_instances["products_operation"].refresh_screen();
                }
            })
        },
        _save_to_server: function (orders, options) {
            var self = this;
            var res = _super_posmodel._save_to_server.call(this, orders, options);
            if (!this.product_need_update_stock_ids) {
                this.product_need_update_stock_ids = [];
            }
            if (orders.length) {
                for (var n = 0; n < orders.length; n++) {
                    var order = orders[n]['data'];
                    for (var i = 0; i < order.lines.length; i++) {
                        var line = order.lines[i][2];
                        var product_id = line['product_id'];
                        var product = this.db.get_product_by_id(product_id);
                        if (product.type == 'product') {
                            this.product_need_update_stock_ids.push(product_id);
                        }
                        if (line.variant_ids && line.variant_ids.length) {
                            var variant_ids = line.variant_ids[0][2];
                            var product_variant_ids = _.map(variant_ids, function (variant_id) {
                                var variant = self.variant_by_id[variant_id];
                                if (variant) {
                                    var product = self.db.get_product_by_id(variant.product_id[0]);
                                    if (product && product.type == 'product') {
                                        return product.id
                                    }
                                }
                            });
                            this.product_need_update_stock_ids = this.product_need_update_stock_ids.concat(product_variant_ids)
                        }
                        if (line.combo_item_ids && line.combo_item_ids.length) {
                            var combo_item_ids = line.combo_item_ids[0][2];
                            var product_combo_item_ids = _.map(combo_item_ids, function (combo_item_id) {
                                var combo_item = self.combo_item_by_id[combo_item_id];
                                if (combo_item) {
                                    var product = self.db.get_product_by_id(combo_item.product_id[0]);
                                    if (product && product.type == 'product') {
                                        return product.id
                                    }
                                }
                            });
                            this.product_need_update_stock_ids = this.product_need_update_stock_ids.concat(product_combo_item_ids)
                        }
                    }
                }
            }
            res.done(function (order_ids) {
                if (self.product_need_update_stock_ids.length) {
                    self._do_update_quantity_onhand(self.product_need_update_stock_ids).done(function () {
                        self.product_need_update_stock_ids= [];
                    });
                }
            });
            return res;
        },
    });

});
