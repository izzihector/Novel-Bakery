odoo.define('pos_restaurant_base.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');

    var QWeb = core.qweb;

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_dirty: function(dirty) {
            //  DIFFERENCES FROM ORIGINAL:
            // * check mp_dirty to avoid repeated orderline rendering
            //   (https://github.com/odoo/odoo/pull/23266)
            //
            // * using orderline_change_line function instead trigger
            //   allows you to avoid unnecessary multiple calls of the same functions
            if (this.mp_dirty !== dirty) {
                this.mp_dirty = dirty;
                if (this.pos.gui.screen_instances.products) {
                    this.pos.gui.screen_instances.products.order_widget.orderline_change_line(this);
                }
            }
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        build_line_resume: function(){
            var resume = {};
            var self = this;
            this.orderlines.each(function(line){
                if (line.mp_skip) {
                    return;
                }
                var line_hash = line.get_line_diff_hash();

                // DIFFERENCES FROM ORIGINAL:
                // * getting qty, note, product_id is moved to a separate function
                // * add line_id value
                var line_resume = self.get_line_resume(line);

                if (typeof resume[line_hash] === 'undefined') {
                    resume[line_hash] = line_resume;
                } else {
                    resume[line_hash].qty += line_resume.qty;
                }
            });
            return resume;
        },
        get_line_resume: function(line) {
            var qty  = Number(line.get_quantity());
            var note = line.get_note();
            var product_id = line.get_product().id;
            var product_name_wrapped = line.generate_wrapped_product_name();
            var line_id = line.id;
            var unit = line.get_unit().name;
            return {qty: qty, note: note, product_id: product_id, product_name_wrapped: product_name_wrapped, line_id: line_id, unit: unit};
        },
        computeChanges: function(categories, config){
            //  DIFFERENCES FROM ORIGINAL: 
            // * new incomming argument "config" (printer config)
            //   it's not used here, but may be used in extension 
            //   (yes, we know that declaration of config is not necessary here,
            //   but we'd like to do it to make code more readable)
            //
            // * new attributes in return: new_all and cancelled_all - lines without filtration with categories
            // * new attributes in return: line_id - id the changed line
            // * new attributes in return: unit - product unit of line
            
            var d = new Date();
            var hours = '' + d.getHours();
            hours = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
            minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

            var current_res = this.build_line_resume();
            var old_res     = this.saved_resume || {};
            var json        = this.export_as_JSON();
            var add = [];
            var rem = [];
            var line_hash;

            for ( line_hash in current_res) {

                var curr = current_res[line_hash];
                var old  = old_res[line_hash];
                var product = this.pos.db.get_product_by_id(curr.product_id);
                var pos_categ_id = product.pos_categ_id;
                if (pos_categ_id.length) {
                    pos_categ_id = pos_categ_id[1]
                }

                if (typeof old === 'undefined') {
                    
                    add.push({
                        'sequence_number': this.sequence_number,
                        'order_uid': json.uid,
                        'id': curr.product_id,
                        'english_name': product.english_name,
                        'uid': curr.uid,
                        'name': product.display_name,
                        'name_wrapped': curr.product_name_wrapped,
                        'note': curr.note,
                        'qty': curr.qty,
                        'unit': curr.unit,
                        'line_id':  curr.line_id,
                        'uom': curr.uom,
                        'variants': curr.variants,
                        'tags': curr.tags,
                        'combo_items': curr.combo_items,
                        'state': curr.state,
                        'category': pos_categ_id,
                        'time': hours + ':' + minutes,
                    });

                } else if (old.qty < curr.qty) {
        
                    add.push({
                        'sequence_number': this.sequence_number,
                        'order_uid': json.uid,
                        'id': curr.product_id,
                        'english_name': product.english_name,
                        'uid': curr.uid,
                        'name': product.display_name,
                        'name_wrapped': curr.product_name_wrapped,
                        'note': curr.note,
                        'qty': curr.qty - old.qty,
                        'uom': curr.uom,
                        'variants': curr.variants,
                        'tags': curr.tags,
                        'line_id':  curr.line_id,
                        'unit':     curr.unit,
                        'combo_items': curr.combo_items,
                        'state': curr.state,
                        'category': pos_categ_id,
                        'time': hours + ':' + minutes,
                    });

                } else if (old.qty > curr.qty) {
                    
                    rem.push({
                        'sequence_number': this.sequence_number,
                        'order_uid': json.uid,
                        'id': curr.product_id,
                        'english_name': product.english_name,
                        'uid': curr.uid,
                        'name': product.display_name,
                        'name_wrapped': curr.product_name_wrapped,
                        'note': curr.note,
                        'qty': old.qty - curr.qty,
                        'uom': curr.uom,
                        'line_id':  curr.line_id,
                        'unit':     curr.unit,
                        'variants': curr.variants,
                        'tags': curr.tags,
                        'combo_items': curr.combo_items,
                        'state': 'Cancelled',
                        'category': pos_categ_id,
                        'time': hours + ':' + minutes,
                    });
                }
            }

            for (line_hash in old_res) {
                if (typeof current_res[line_hash] === 'undefined') {
                    var old = old_res[line_hash];
                    var product = this.pos.db.get_product_by_id(old.product_id);
                    var pos_categ_id = product.pos_categ_id;
                    if (pos_categ_id.length) {
                        pos_categ_id = pos_categ_id[1]
                    }
                    
                    rem.push({
                        'sequence_number': this.sequence_number,
                        'order_uid': json.uid,
                        'id': old.product_id,
                        'english_name': product.english_name,
                        'uid': old.uid,
                        'name': this.pos.db.get_product_by_id(old.product_id).display_name,
                        'name_wrapped': old.product_name_wrapped,
                        'note': old.note,
                        'qty': old.qty,
                        'uom': old.uom,
                        'line_id':  old.line_id,
                        'unit':     old.unit,
                        'variants': old.variants,
                        'tags': old.tags,
                        'combo_items': old.combo_items,
                        'state': 'Cancelled',
                        'category': pos_categ_id,
                        'time': hours + ':' + minutes,
                    }); 
                }
            }

            var new_all = add;
            var cancelled_all = rem;

            if(categories && categories.length > 0){
                // filter the added and removed orders to only contains
                // products that belong to one of the categories supplied as a parameter

                var self = this;

                var _add = [];
                var _rem = [];

                for(var i = 0; i < add.length; i++){
                    if(self.pos.db.is_product_in_category(categories,add[i].id)){
                        _add.push(add[i]);
                    }
                }
                add = _add;

                for(var i = 0; i < rem.length; i++){
                    if(self.pos.db.is_product_in_category(categories,rem[i].id)){
                        _rem.push(rem[i]);
                    }
                }
                rem = _rem;
            }

            var d = new Date();
            var hours   = '' + d.getHours();
                hours   = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
                minutes = minutes.length < 2 ? ('0' + minutes) : minutes;

            return {
                'new_all': new_all,
                'cancelled_all': cancelled_all,
                'guest_number': json['guest_number'],
                'guest': json['guest'],
                'note': json['note'],
                'uid': json['uid'],
                'sequence_number': json['sequence_number'],
                'new': add,
                'cancelled': rem,
                'table': json.table || false,
                'floor': json.floor || false,
                'name': json.name || 'unknown order',
                'time': {
                    'hours': hours,
                    'minutes': minutes,
                },
            };
        },
        
        hasChangesToPrint: function(){
            var printers = this.pos.printers;
            for(var i = 0; i < printers.length; i++){
                //  DIFFERENCES FROM ORIGINAL: call compute change with config
                var changes = this.computeChanges(printers[i].config.product_categories_ids, printers[i].config);
                if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                    return true;
                }
            }
            return false;
        },
    });
    return models;
});
