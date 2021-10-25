odoo.define('pos_retail_restaurant.screen_kitchen', function (require) {
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var qweb = core.qweb;
    var chrome = require('point_of_sale.chrome');
    var db = require('point_of_sale.DB');
    var retail_restaurant = require('pos_retail.restaurant');
    var models = require('point_of_sale.models');

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_notifications: function (message) {
            var action = message['action'];
            var is_not_waiter = false;
            if (this.config.screen_type && this.config.screen_type != 'waiter') {
                is_not_waiter = true;
            }
            if (is_not_waiter && ['set_state', 'request_printer', 'line_removing', 'unlink_order', 'paid_order'].indexOf(action) == -1) {
                return
            }
            _super_posmodel.get_notifications.apply(this, arguments);
            if (is_not_waiter && action == 'unlink_order') {
                this.trigger('event:sync_order_removing', message.data, 'Cancelled'); // TODO: for kitchen waiters and kitchen chef
            }
            if (is_not_waiter && action == 'paid_order') {
                this.trigger('event:sync_order_removing', message.data, 'Done'); // TODO: for kitchen waiters and kitchen chef
            }
            console.log('Get action: ', action)
        },
    });

    db.include({
        save_kitchen_order: function (order) {
            var kitchen_orders = this.load('kitchen_orders', []);
            var kitchen_orders = _.filter(kitchen_orders, function (cached_order) {
                return cached_order.uid != order.uid
            });
            kitchen_orders.push(order);
            this.save('kitchen_orders', kitchen_orders);
        },
        get_kitchen_orders: function () {
            var kitchen_orders = this.load('kitchen_orders', []);
            return kitchen_orders
        }
    });

    var KitchenScreen = screens.ScreenWidget.extend({
        template: 'kitchen_screen',
        show_numpad: false,
        show_leftpane: true,
        previous_screen: false,

        init: function (parent, options) {
            this.last_line_uid = null;
            this.lines_selected = [];
            this.orders = self.posmodel.db.get_kitchen_orders();
            this._super(parent, options);
        },
        start: function () {
            var self = this;
            this._super();
            self.reverse = false;
            this.pos.bind('reload:kitchen_screen', function () {
                self.renderElement();
            });
            this.pos.bind('event:line-state', function (vals) {
                self.update_state(vals['uid'], vals['state'])
            });
            this.pos.bind('event:sync_order_removing', function (order_uid, state) {
                self.update_state_from_order_uid(order_uid, state)
            });
            this.pos.bind('save:new_transactions', function (new_transactions, screen_type) {
                if (new_transactions['new'].length || new_transactions['cancelled'].length) {
                    self.save_data_items(new_transactions, screen_type)
                }
            });
            this.pos.bind('sort:screen', function (sort_type) {
                if (sort_type == self.last_sort_type) {
                    self.orders = self.orders.sort(self.pos.sort_by(sort_type, false, function (a) {
                        if (!a) {
                            a = 'N/A';
                        }
                        return a.toUpperCase()
                    }));
                } else {
                    self.orders = self.orders.sort(self.pos.sort_by(sort_type, true, function (a) {
                        if (!a) {
                            a = 'N/A';
                        }
                        return a.toUpperCase()
                    }));
                }
                self.last_sort_type = sort_type;
                self.renderElement()
            });
        },
        show: function () {
            var self = this;
            this._super();
            this.$('.back').click(function () {
                self.gui.show_screen('products');
            });
            if (this.pos.config.screen_type != 'waiter') {
                $(document).keydown(function (event) { // TODO: only for iotbox
                    var key = event.which;
                    self.press_keyboard(key);
                });
            }
        },
        scroll_to_box: function (uid) {
            document.querySelector("[data-id='" + uid + "']").scrollIntoView({behavior: 'smooth'});
        },
        auto_select_line: function () {
            var items = this.get_all_items();
            if (items.length) {
                if (!this.last_line_uid) {
                    var first_item = items[0];
                    var uid = first_item['uid'];
                    this.select_line(uid);
                } else {
                    var found_the_same_order = false;
                    for (var i = 0; i < items.length; i++) {
                        var item = items[i];
                        var last_order_uid = this.get_order_uid(this.last_line_uid);
                        var next_order_uid = this.get_order_uid(item['uid']);
                        if (last_order_uid == next_order_uid) {
                            this.select_line(item['uid']);
                            found_the_same_order = true;
                            break
                        }
                    }
                    if (!found_the_same_order) {
                        this.last_line_uid = null;
                        this.auto_select_line()
                    }
                }
            }
        },
        get_all_items: function () {
            var items = [];
            for (var i = 0; i < this.orders.length; i++) {
                var data = this.orders[i];
                if (data['cancelled'].length) {
                    items = items.concat(data['cancelled'])
                }
                if (data['new'].length) {
                    items = items.concat(data['new'])
                }
            }
            return items;
        },
        get_order_uid: function (line_uid) {
            var order_uid = '';
            var array_uid = line_uid.split('-');
            for (var i = 0; i < 3; i++) {
                if (!order_uid) {
                    order_uid += array_uid[i];
                } else {
                    order_uid += '-' + array_uid[i];
                }
            }
            return order_uid
        },
        press_keyboard: function (input) {
            // TODO: Keyboard events
            //  1               Up: 38
            //  2               Down: 40
            //  3               Left: 37
            //  4               Right: 39
            //  5               Pause: 52 (4)
            //  6               Refresh: 53 (5)
            //  7               Line Done: 13 (enter)
            //  8               Order Done: 16 (shift)
            //  8               Order Done: 16 (shift)
            //  9               Language A/spare
            //  0               Language B/spare
            console.log(input);
            var items = this.get_all_items();
            if (this.lines_selected.length == 0 && items.length) {
                this.auto_select_line()
            } else {
                var uid_selected = this.lines_selected[0];
                if (!uid_selected) {
                    return false
                }
                var current_order_uid = this.get_order_uid(uid_selected);
                if (input == 13 || input == 104) { // TODO: order done 13(enter), 104: special keycode
                    if (this.lines_selected.length) {
                        var line_uid = this.lines_selected[0];
                        this.line_ready_to_transfer(line_uid);
                    }
                }
                if (input == 37 || input == 102 || input == 52) { // TODO: move Left
                    for (var i = 0; i < items.length; i++) {
                        if (i >= 1) {
                            var last_order_uid = this.get_order_uid(items[i - 1]['uid']);
                            var next_order_uid = this.get_order_uid(items[i]['uid']);
                            if (current_order_uid != last_order_uid && current_order_uid == next_order_uid) {
                                var last_uid = items[i - 1]['uid'];
                                this.select_line(last_uid);
                                this.scroll_to_box(last_uid);
                                break
                            }
                        }
                    }
                }
                if (input == 39 || input == 100 || input == 54) { //TODO: move Right
                    var meet_order = false;
                    for (var i = 0; i < items.length; i++) {
                        var data = items[i];
                        var next_order_uid = this.get_order_uid(data['uid']);
                        if (current_order_uid == next_order_uid) {
                            meet_order = true
                            continue
                        }
                        if (current_order_uid != next_order_uid && meet_order) {
                            var next_uid = data['uid'];
                            this.select_line(next_uid);
                            this.scroll_to_box(next_uid);
                            break
                        }
                    }
                }
                if (input == 38 || input == 104 || input == 56) { // TODO: move Up
                    for (var i = 0; i < items.length; i++) {
                        var data = items[i];
                        if (uid_selected == data['uid']) {
                            if (i == 0) {
                                var next_uid = items[items.length - 1]['uid'];
                            } else {
                                var next_uid = items[i - 1]['uid'];
                            }
                            this.select_line(next_uid);
                            this.scroll_to_box(next_uid);
                            break
                        }
                    }
                }
                if (input == 40 || input == 98 || input == 50) { //TODO: move Down
                    for (var i = 0; i < items.length; i++) {
                        var data = items[i];
                        if (uid_selected == data['uid']) {
                            if ((i + 1) == items.length) {
                                var next_uid = items[0]['uid'];
                            } else {
                                var next_uid = items[i + 1]['uid'];
                            }
                            this.select_line(next_uid);
                            this.scroll_to_box(next_uid);
                        }
                    }
                }
                if (input == 53 || input == 104 || input == 102) { // TODO: refresh screen
                    this.gui.chrome.widget['refresh_screen_widget'].el.click();
                }
                if (input == 46) { // TODO: 46 = del button
                    var lines_of_order = _.filter(items, function (data) {
                        return data['order_uid'] == current_order_uid
                    });
                    for (var i = 0; i < lines_of_order.length; i++) {
                        this.line_ready_to_transfer(lines_of_order[i]['uid'])
                    }
                }
            }
        },
        select_line: function (line_uid) {
            this.$(".line-select").removeClass('item-selected');
            var $row_selected = this.$("[data-id='" + line_uid + "']");
            $row_selected.addClass('item-selected');
            this.lines_selected = [line_uid];
        },
        allow_display: function (product_id) {
            var allow_display = true;
            var sync_between_iot_boxes = this.pos.config.sync_multi_session_offline;
            var product_allow_display = [];
            if (this.pos.iot_boxes) {
                for (var i = 0; i < this.pos.iot_boxes.length; i++) {
                    product_allow_display = product_allow_display.concat(this.pos.iot_boxes[i].product_ids)
                }
            }
            if (!sync_between_iot_boxes) {
                if (this.pos.config.display_all_product) {
                    return true
                } else {
                    var display = this.pos.db.is_product_in_category(this.pos.config.product_categ_ids, product_id);
                    if (display) {
                        return true
                    } else {
                        return false
                    }
                }
            } else {
                if (product_allow_display.indexOf(product_id) == -1) {
                    return false
                }
            }
            return allow_display
        },
        save_data_items: function (new_transactions) {
            var items_new = [];
            var items_cancelled = [];
            for (var z = 0; z < new_transactions['new'].length; z++) {
                var line = new_transactions['new'][z];
                var allow_display = this.allow_display(line.id);
                if (allow_display) {
                    items_new.push(line)
                }
            }
            for (var z = 0; z < new_transactions['cancelled'].length; z++) {
                var line = new_transactions['cancelled'][z];
                var allow_display = this.allow_display(line.id);
                if (allow_display) {
                    items_cancelled.push(line)
                }
            }
            new_transactions['new'] = items_new;
            new_transactions['cancelled'] = items_cancelled;
            var last_order = _.find(this.orders, function (data) {
                return data['uid'] == new_transactions['uid']
            });
            if (last_order) { // TODO: unique by order uid, if still have order requested before, we merge to one box
                new_transactions['new'] = new_transactions['new'].concat(last_order['new']);
                new_transactions['cancelled'] = new_transactions['cancelled'].concat(last_order['cancelled']);
                this.orders = _.filter(this.orders, function (data) {
                    return data['uid'] != last_order['uid']
                })
            }
            if (new_transactions['new'].length || new_transactions['cancelled'].length) {
                this.orders.push(new_transactions);
            }
            if (items_new.length || items_cancelled.length) {
                this.renderElement();
            }
        },
        renderElement: function () {
            var self = this;
            this._super();
            if (this.orders) {
                this.render_orders();
                this.line_actions();
            } else {
                this.$('.lines-list').empty()
            }
            this.$('.line-select').click(function () {
                var line_uid = $(this).data('id');
                self.select_line(line_uid);
            });
        },
        update_state: function (line_uid, state) {
            var line_updated = [];
            var new_orders = [];
            for (var i = 0; i < this.orders.length; i++) {
                var new_items = this.orders[i]['new'];
                var cancelled_items = this.orders[i]['cancelled'];
                var keep_live = false;
                var new_items_updated = [];
                var cancelled_items_updated = [];
                for (var j = 0; j < new_items.length; j++) {
                    var new_item = new_items[j];
                    if (new_item.uid == line_uid) {
                        if (state == 'Done') {
                            line_updated.push(new_item)
                        } else {
                            keep_live = true;
                            new_item['state'] = state;
                            new_items_updated.push(new_item);
                        }
                    } else {
                        keep_live = true;
                        new_items_updated.push(new_item);
                    }
                }
                if (new_items_updated.length) {
                    this.orders[i]['new'] = new_items_updated
                } else {
                    this.orders[i]['new'] = []
                }
                for (var j = 0; j < cancelled_items.length; j++) {
                    var cancelled_item = cancelled_items[j];
                    if (cancelled_item.uid == line_uid) {
                        line_updated.push(cancelled_item)
                    } else {
                        keep_live = true;
                        cancelled_items_updated.push(cancelled_item);
                    }
                }
                if (cancelled_items_updated.length) {
                    this.orders[i]['cancelled'] = cancelled_items_updated
                } else {
                    this.orders[i]['cancelled'] = []
                }
                if (keep_live && (this.orders[i]['new'].length || this.orders[i]['cancelled'].length)) {
                    new_orders.push(this.orders[i])
                }
            }
            this.orders = new_orders;
            this.renderElement();
        },
        update_state_from_order_uid: function (order_uid, state) {
            for (var i = 0; i < this.orders.length; i++) {
                var new_items = this.orders[i]['new'];
                var cancelled_items = this.orders[i]['cancelled'];
                for (var j = 0; j < new_items.length; j++) {
                    var new_item = new_items[j];
                    if (new_item.order_uid == order_uid) {
                        new_item.state = state;
                        this.update_state(new_item.uid, state);
                    }
                }
                for (var j = 0; j < cancelled_items.length; j++) {
                    var cancelled_item = cancelled_items[j];
                    if (cancelled_item.order_uid == order_uid) {
                        new_item.state = state;
                        this.update_state(new_item.uid, state);
                    }
                }
            }
        },
        line_ready_to_transfer: function (line_uid) {
            this.last_line_uid = line_uid;
            var screen_type = this.pos.config.screen_type;
            var line_updated = [];
            var new_orders = [];
            for (var i = 0; i < this.orders.length; i++) {
                var new_items = this.orders[i]['new'];
                var cancelled_items = this.orders[i]['cancelled'];
                var keep_live = false;
                var new_items_updated = [];
                var cancelled_items_updated = [];
                for (var j = 0; j < new_items.length; j++) {
                    var new_item = new_items[j];
                    if (new_item.uid == line_uid) {
                        line_updated.push(new_item)
                    } else {
                        keep_live = true;
                        new_items_updated.push(new_item);
                    }
                }
                if (new_items_updated.length) {
                    this.orders[i]['new'] = new_items_updated
                } else {
                    this.orders[i]['new'] = []
                }
                for (var j = 0; j < cancelled_items.length; j++) {
                    var cancelled_item = cancelled_items[j];
                    if (cancelled_item.uid == line_uid) {
                        line_updated.push(cancelled_item)
                    } else {
                        keep_live = true;
                        cancelled_items_updated.push(cancelled_item);
                    }
                }
                if (cancelled_items_updated.length) {
                    this.orders[i]['cancelled'] = cancelled_items_updated
                } else {
                    this.orders[i]['cancelled'] = []
                }
                if (keep_live && (this.orders[i]['new'].length || this.orders[i]['cancelled'].length)) {
                    new_orders.push(this.orders[i])
                }
            }
            this.orders = new_orders;
            if (screen_type == 'kitchen') {
                this.pos.pos_bus.set_state(line_uid, 'Ready', line_updated);
            }
            if (screen_type == 'kitchen_waiter') {
                this.pos.pos_bus.set_state(line_uid, 'Done', line_updated);
            }
            this.lines_selected = [];
            this.renderElement();
            this.auto_select_line();

        },
        line_actions: function () {
            var self = this;
            this.$('.kitchen_delivery').click(function () {
                var line_uid = $(this).parent().parent().data()['id'];
                self.line_ready_to_transfer(line_uid);
            });
        },
        render_orders: function () {
            for (var i = 0; i < this.orders.length; i++) {
                var order = this.orders[i];
                if (order['new'].length == 0 && order['cancelled'].length == 0) {
                    continue;
                }
                this.pos.db.save_kitchen_order(order);
                var line_html = qweb.render('kitchen_box', {
                    widget: this,
                    order: order
                });
                var line_cache = document.createElement('div');
                line_cache.innerHTML = line_html;
                line_cache = line_cache.childNodes[1];
                this.$el[0].querySelector('.lines-list').appendChild(line_cache);
            }
            if (this.pos.config.play_sound) {
                this.pos.play_sound();
            }
        }
    });

    gui.define_screen({
        'name': 'kitchen_screen',
        'widget': KitchenScreen,
    });

    var refresh_screen_widget = chrome.StatusWidget.extend({
        template: 'refresh_screen_widget',
        start: function () {
            var self = this;
            this.pos.bind('change:refresh_kitchen_screen', function (pos, sync_between_sessions) {
                self.set_status(sync_between_sessions.state, sync_between_sessions.pending);
            });
        },
    });


    chrome.Chrome.include({
        build_widgets: function () {
            if (this.pos.pos_bus && (this.pos.config.screen_type == 'kitchen_waiter' || this.pos.config.screen_type == 'kitchen')) {
                this.widgets.push(
                    {
                        'name': 'refresh_screen_widget',
                        'widget': refresh_screen_widget,
                        'append': '.pos-rightheader'
                    }
                );
            }
            this._super();
        }
    });
});