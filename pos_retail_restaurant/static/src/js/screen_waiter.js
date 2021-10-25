odoo.define('pos_retail_restaurant.kitchen_waiter', function (require) {
    var screens = require('point_of_sale.screens');
    var floors = require('pos_restaurant.floors');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var qweb = core.qweb;
    var models = require('point_of_sale.models');

    var button_kitchen_receipt_screen = screens.ActionButtonWidget.extend({
        template: 'button_kitchen_receipt_screen',
        button_click: function () {
            var order = this.pos.get('selectedOrder');
            if (order) {
                this.pos.gui.show_screen('kitchen_receipt_screen');
            } else {
                this.pos.gui.show_popup('dialog', {
                    title: 'Warning',
                    body: 'Nothing order for render data print'
                })
            }
        }
    });
    screens.define_action_button({
        'name': 'button_kitchen_receipt_screen',
        'widget': button_kitchen_receipt_screen,
        'condition': function () {
            return this.pos.config.kitchen_receipt;
        }
    });

    var button_set_lines_to_done = screens.ActionButtonWidget.extend({
        template: 'button_set_lines_to_done',
        button_click: function () {
            var order = this.pos.get('selectedOrder');
            if (order) {
                var updated = false;
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    var line = order.orderlines.models[i];
                    if (line.state == 'Ready') {
                        line.set_state('Done');
                        updated = true
                    }
                }
                if (!updated) {
                    this.pos.gui.show_popup('dialog', {
                        title: 'Warning',
                        body: 'Have not any lines need to delivery'
                    })
                }
            }
        }
    });
    screens.define_action_button({
        'name': 'button_set_lines_to_done',
        'widget': button_set_lines_to_done,
        'condition': function () {
            return this.pos.config.set_lines_to_done;
        }
    });

    screens.OrderWidget.include({
        remove_orderline: function (order_line) {
            var res = this._super(order_line);
            if ((order_line.syncing == false || !order_line.syncing) && this.pos.pos_bus) {
                order_line.trigger_line_removing();
            }
            return res
        },
        update_summary: function () {
            try {
                this._super();
                var order = this.pos.get_order();
                var buttons = this.getParent().action_buttons;
                var printers = this.pos.printers;
                var changed = false;
                if (order) {
                    for (var i = 0; i < printers.length; i++) {
                        var changes = order.computeChanges(printers[i].config.product_categories_ids);
                        if (changes['new'].length > 0 || changes['cancelled'].length > 0) {
                            changed = true;
                        }
                    }
                }
                if (order && buttons && buttons.button_delivery_to_kitchen) {
                    var missed_request_kitchen = this.pos.get_order().get_lines_missed_request_kitchen();
                    if (!this.pos.sync_status || !missed_request_kitchen) {
                        buttons.button_delivery_to_kitchen.highlight(false);
                    } else {
                        buttons.button_delivery_to_kitchen.highlight(true);
                    }
                    if (changed) {
                        buttons.button_delivery_to_kitchen.highlight(true);
                    }
                }
                if (order && buttons && buttons.button_set_lines_to_done) {
                    var has_lines_delivery = this.pos.get_order().get_lines_need_delivery();
                    if (!has_lines_delivery) {
                        buttons.button_set_lines_to_done.highlight(false);
                    } else {
                        buttons.button_set_lines_to_done.highlight(true);
                    }
                }
            } catch (e) {

            }

        },
        render_orderline: function (orderline) {
            var el_node = this._super(orderline);
            if (!el_node) {
                return el_node
            }
            var done_button = el_node.querySelector('.done');
            if (done_button) {
                done_button.addEventListener('click', function () {
                    orderline.set_state('Done');
                });
            }
            var priority_button = el_node.querySelector('.priority');
            if (priority_button) {
                priority_button.addEventListener('click', function () {
                    orderline.set_state('Priority');
                });
            }
            var exit_priority_button = el_node.querySelector('.exit_priority');
            if (exit_priority_button) {
                exit_priority_button.addEventListener('click', function () {
                    orderline.set_state('Waiting');
                });
            }
            var pending_button = el_node.querySelector('.pending');
            if (pending_button) {
                pending_button.addEventListener('click', function () {
                    orderline.set_state('Pending');
                });
            }
            return el_node;
        }
    });

    floors.TableWidget.include({
        init: function (parent, options) {
            this.pos = parent.pos;
            this._super(parent, options);
        },
        get_order_by_widget: function () {
            var self = this;
            var orders = this.pos.get('orders').models;
            var orders_created = _.filter(orders, function (o) {
                return o.table && o.table.id == self.table.id
            });
            return orders_created;
        },
        get_waiting_delivery: function () {
            var orders_created = this.get_order_by_widget();
            if (orders_created.length) {
                var count = 0;
                for (var n = 0; n < orders_created.length; n++) {
                    var order = orders_created[n];
                    for (var i = 0; i < order.orderlines.models.length; i++) {
                        var line = order.orderlines.models[i];
                        if (line.state == 'Ready') {
                            count += 1;
                        }
                    }
                }

                return count;
            } else {
                return 0;
            }
        },
        get_total_amount_by_table: function () {
            var orders_created = this.get_order_by_widget();
            var amount = 0;
            if (orders_created) {
                for (var n = 0; n < orders_created.length; n++) {
                    var order = orders_created[n];
                    amount += order.get_total_with_tax()
                }
            }
            return amount;
        },
        missed_request_kitchen: function () {
            var orders_created = this.get_order_by_widget();
            if (orders_created) {
                var count = 0;
                for (var n = 0; n < orders_created.length; n++) {
                    var order = orders_created[n];
                    for (var i = 0; i < order.orderlines.models.length; i++) {
                        var line = order.orderlines.models[i];
                        if (line.state == 'Draft') {
                            count += 1;
                        }
                    }
                }
                return count;
            } else {
                return 0;
            }
        }
    });

    var button_print_last_submit_order = screens.ActionButtonWidget.extend({
        template: 'button_print_last_submit_order',
        button_click: function () {
            var order = this.pos.get('selectedOrder');
            if (order) {
                order.reprint_last_receipt_kitchen();
            }
        }
    });

    screens.define_action_button({
        'name': 'button_print_last_submit_order',
        'widget': button_print_last_submit_order,
        'condition': function () {
            return this.pos.config.screen_type && this.pos.config.screen_type !== 'kitchen' && this.pos.config.screen_type !== 'kitchen_waiter' && this.pos.config.print_last_submit_order;
        }
    });

    var button_delivery_to_kitchen = screens.ActionButtonWidget.extend({
        template: 'button_delivery_to_kitchen',
        button_click: function () {
            var order = this.pos.get('selectedOrder');
            if (order) {
                order.saveChanges();
            }
        }
    });
    screens.define_action_button({
        'name': 'button_delivery_to_kitchen',
        'widget': button_delivery_to_kitchen,
        'condition': function () {
            return this.pos.config.screen_type && this.pos.config.screen_type !== 'kitchen' && this.pos.config.screen_type !== 'kitchen_waiter' && this.pos.config.send_order_to_kitchen;
        }
    });

    var reboot_iot_box = screens.ActionButtonWidget.extend({
        template: 'reboot_iot_box',
        button_click: function () {
            var self = this;
            this.pos.gui.show_popup('confirm', {
                title: 'Warning',
                body: 'All IoT Boxes config at Sync between Session will Reboot, Are you wanted do it now ?',
                confirm: function () {
                    for (var i = 0; i < self.pos.iot_connections.length; i++) { //
                        var iot_connection = self.pos.iot_connections[i];
                        var params = {};
                        var sending_iot = iot_connection.rpc("/pos/reboot", params, {shadow: true});
                        sending_iot.then(function (results) {
                            self.pos.gui.show_popup('dialog', {
                                title: 'Succeed',
                                body: 'All your IoT will reboot few seconds later',
                                color: 'success'
                            })
                        }, function (error) {
                            self.pos.gui.show_popup('dialog', {
                                title: 'Succeed',
                                body: 'All your IoT will reboot few seconds later',
                                color: 'success'
                            })
                        })
                    }
                }
            })
        }
    });
    screens.define_action_button({
        'name': 'reboot_iot_box',
        'widget': reboot_iot_box,
        'condition': function () {
            return this.pos.iot_connections && this.pos.iot_connections.length > 0 && this.pos.debug
        }
    });

    var kitchen_receipt_screen = screens.ScreenWidget.extend({
        template: 'kitchen_receipt_screen',
        show: function () {
            this._super();
            this.render_receipt();
        },
        lock_screen: function (locked) {
            this._locked = locked;
            if (locked) {
                this.$('.next').removeClass('highlight');
            } else {
                this.$('.next').addClass('highlight');
            }
        },
        get_receipt_filter_by_printer_render_env: function (printer) {
            var order = this.pos.get_order();
            var item_new = [];
            var item_cancelled = [];
            var changes = order.computeChanges(printer.config.product_categories_ids);
            for (var i = 0; i < changes['new'].length; i++) {
                item_new.push(changes['new'][i]);
            }
            for (var i = 0; i < changes['cancelled'].length; i++) {
                item_cancelled.push(changes['cancelled'][i]);
            }
            
            // Changes By Mushahid Ali Start
            var d = new Date();
            var y = d.getFullYear();
            var m = d.getMonth();
            m = m < 10 ? '0'+m : m;
            var da = d.getDate();
            da = da < 10 ? '0'+da : da;
            var h = d.getHours();
            var ampm = h >= 12 ? 'PM' : 'AM';
            h = h % 12;
            h = h ? h : 12;
            h = h < 10 ? '0'+h : h;
            var mi = d.getMinutes();
            mi = mi < 10 ? '0'+mi : mi;
            var s = d.getSeconds();
            s = s < 10 ? '0'+s : s;
            var datetime =  y+"/"+m+"/"+da+" "+h+":"+mi+":"+s+" "+ampm;
            var date_only = y+"/"+m+"/"+da;
            var time_only = h+":"+mi+":"+s+" "+ampm;
            console.log("000000000000000000000000000000000000000000000000000000000000000");
            console.log("items_new",item_new);
            console.log("object",this);
            console.log("chnages",changes);
            console.log("orders",order);
            console.log("orders",order['customer_count']);
            return {
                widget: this,
                table: changes['table'] || null,
                floor: changes['floor'] || null,
                new_items: item_new,
                cancelled_items: item_cancelled,
                name: changes['name'],
                time: changes['time'],
                datetime: datetime,
                date_only:date_only,
                guest_numbers:order['customer_count'],
                time_only:time_only
            }
            // Changes By Mushahid Ali End
        },
        print_web: function () {
            var self = this;
            this.lock_screen(true);
            setTimeout(function () {
                self.lock_screen(false);
            }, 1000);
            window.print();
        },
        click_back: function () {
            this.pos.gui.show_screen('products');
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.back').click(function () {
                self.click_back();
            });
            this.$('.button.print-kitchen-receipt').click(function () {
                self.print_web();
            });
        },
        render_receipt: function () {
            this.$('.pos-receipt-container').empty();
            var printers = this.pos.printers;
            for (var i = 0; i < printers.length; i++) {
                var value = this.get_receipt_filter_by_printer_render_env(printers[i]);
                if (value['new_items'].length > 0 || value['cancelled_items'].length > 0) {
                    this.$('.pos-receipt-container').append(qweb.render('kitchen_receipt_html', value));
                }
            }
            this.pos.get_order().saveChanges();
        }
    });

    gui.define_screen({name: 'kitchen_receipt_screen', widget: kitchen_receipt_screen});

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        can_be_merged_with: function (orderline) {
            return (this.state == 'Draft') && _super_orderline.can_be_merged_with.apply(this, arguments);
        },
    });

});
