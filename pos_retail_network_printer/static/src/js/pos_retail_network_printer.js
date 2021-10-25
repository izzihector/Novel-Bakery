"use strict";
odoo.define('pos_retail_network_printer.multi_epson_printer', function (require) {

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var qweb = core.qweb;
    var screens = require('point_of_sale.screens');
    var retail_screens = require('pos_retail.screens');
    var Session = require('web.Session');
    var chrome = require('point_of_sale.chrome');
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var devices = require('point_of_sale.devices');

    devices.ProxyDevice.include({
        print_receipt: function (receipt) {
            if (this.pos.epson_printer_default && receipt && this.pos.gui) {
                this.pos.print_network(receipt, this.pos.epson_printer_default['ip']);
            }
            this._super(receipt);
        },
        keepalive: function () {
            var self = this;
            // TODO: delay 5 seconds, auto call this function for check status of all printers
            function auto_update_status_printer() {
                var printer_ips = [];
                for (var i = 0; i < self.pos.epson_printers.length; i++) {
                    printer_ips.push(self.pos.epson_printers[i]['ip'])
                }
                var params = {
                    printer_ips: printer_ips,
                };
                return self.connection.rpc("/hw_proxy/get_printers_status", params, {
                    shadow: true,
                    timeout: 2500
                }).fail(function (error) {
                    if (error.code == -32098) {
                        console.log('Printers Offline')
                    }
                    self.pos.set('status_printer', {'state': 'disconnected', 'pending': 1});
                }, {timeout: 2500}).done(function (results) {
                    var values = JSON.parse(results)['values'];
                    var online = true;
                    var pending = 0;
                    for (var printer_ip in values) {
                        if (values[printer_ip] == 'Offline') {
                            online = false;
                            pending += 1
                        }
                        var epson_printer = _.find(self.pos.epson_printers, function (printer) {
                            return printer['ip'] == printer_ip;
                        });
                        if (epson_printer) {
                            epson_printer['state'] = values[printer_ip]
                        }
                    }
                    if (online == true) {
                        self.pos.set('status_printer', {'state': 'connected', 'pending': 0});
                    } else {
                        self.pos.set('status_printer', {'state': 'disconnected', 'pending': pending});
                    }
                }).always(function () {
                    setTimeout(auto_update_status_printer, 5000);
                });
            }

            if (this.pos.epson_printers.length) {
                auto_update_status_printer();
            }
            this._super();
        },
    });

    var popup_printers_network = PopupWidget.extend({ // select combo
        template: 'popup_printers_network',
        show: function (options) {
            var self = this;
            this.options = options;
            var epson_printers = options.epson_printers;
            this._super(options);
            this.$el.find('.card-content').html(qweb.render('printers_network', {
                epson_printers: epson_printers,
                widget: self
            }));
            $('.cancel').click(function () {
                self.gui.close_popup();
            });
        }
    });
    gui.define_popup({name: 'popup_printers_network', widget: popup_printers_network});

    models.load_models([
        {
            model: 'pos.epson',
            fields: ['name', 'ip', 'auto_print'],
            loaded: function (self, epson_printers) {
                self.epson_printer_default = null;
                self.epson_printers = [];
                self.epson_priner_by_id = {};
                self.epson_priner_by_ip = {};
                for (var i = 0; i < epson_printers.length; i++) {
                    self.epson_priner_by_id[epson_printers[i]['id']] = epson_printers[i];
                    self.epson_priner_by_ip[epson_printers[i]['ip']] = epson_printers[i];
                }
                var printer_id = self.config.printer_id;
                if (printer_id) {
                    var epson_printer_default = _.find(epson_printers, function (epson_printer) {
                        return epson_printer.id == printer_id[0];
                    });
                    if (epson_printer_default) {
                        epson_printer_default['print_receipt'] = true;
                        self.epson_printer_default = epson_printer_default;
                        self.epson_printers.push(epson_printer_default);
                    }
                }
            },
        },
    ], {
        before: 'restaurant.printer'
    });

    var printer_network_widget = chrome.StatusWidget.extend({
        template: 'printer_network_widget',
        start: function () {
            var self = this;
            this.pos.bind('change:status_printer', function (pos, sync_status) {
                self.set_status(sync_status.state, sync_status.pending);
            });
            this.$el.click(function () {
                var printer_ips = [];
                for (var i = 0; i < self.pos.epson_printers.length; i++) {
                    printer_ips.push(self.pos.epson_printers[i]['ip'])
                }
                if (printer_ips.length == 0) {
                    self.pos.set('status_printer', {'state': 'connected', 'pending': 0});
                    return self.gui.show_popup('dialog', {
                        title: 'Warning',
                        body: 'Have not any Printers Epson add to config'
                    })
                }
                var params = {
                    printer_ips: printer_ips,
                };
                if (!self.pos.proxy || !self.pos.proxy.host) {
                    return self.gui.show_popup('dialog', {
                        title: 'Error',
                        body: 'Your pos config not setting POSBOX proxy or posbox offline mode'
                    })
                }
                var connection = new Session(void 0, self.pos.proxy.host, {
                    use_cors: true
                });
                return connection.rpc("/hw_proxy/get_printers_status", params, {
                    shadow: true,
                    timeout: 2500
                }, function (error) {
                    self.pos.set('status_printer', {'state': 'disconnected', 'pending': 1});
                }).then(function (results) {
                    var values = JSON.parse(results)['values'];
                    var online = true;
                    var pending = 0;
                    for (var printer_ip in values) {
                        if (values[printer_ip] == 'Offline') {
                            online = false;
                            pending += 1
                        }
                        var epson_printer = _.find(self.pos.epson_printers, function (printer) {
                            return printer['ip'] == printer_ip;
                        });
                        if (epson_printer) {
                            epson_printer['state'] = values[printer_ip]
                        }
                        if (self.pos.debug) {
                            var receipt = '<div>POS Retail Copyright © 2017 TL Technology. All right reserved. If you need quickly support please email to: thanhchatvn@gmail.com or discuss viva our skype thanhchatvn</div>';
                            for (var n = 0; n < 1; n++) {
                                self.pos.print_network(receipt, printer_ip)
                            }
                        }
                    }
                    self.pos.gui.show_popup('popup_printers_network', {
                        title: 'Status of Printers Network',
                        epson_printers: self.pos.epson_printers,
                    });
                    if (online == true) {
                        self.pos.set('status_printer', {'state': 'connected', 'pending': 0});
                    } else {
                        self.pos.set('status_printer', {'state': 'disconnected', 'pending': pending});
                    }
                })
            });
        },
    });

    chrome.Chrome.include({
        build_widgets: function () {
            if (this.pos.epson_printers) {
                this.widgets.push(
                    {
                        'name': 'printer_network_widget',
                        'widget': printer_network_widget,
                        'append': '.pos-branding'
                    }
                );
            }
            this._super();
        }
    });

    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var base_restaurant_printer_model = this.get_model('restaurant.printer');
            base_restaurant_printer_model.fields.push('printer_id', 'print_type', 'product_category_ids');
            base_restaurant_printer_model.domain = function (self) {
                if (self.config.pos_branch_id) {
                    return [['id', 'in', self.config.printer_ids], ['branch_id', '=', self.config.pos_branch_id[0]]];
                } else {
                    return [['id', 'in', self.config.printer_ids]];
                }
            };
            var _super_restaurant_printer_model_loaded = base_restaurant_printer_model.loaded;
            base_restaurant_printer_model.loaded = function (self, printers) {
                for (var i = 0; i < printers.length; i++) {
                    var printer = printers[i];
                    if (printer['printer_id'] && printer['print_type'] == 'network') {
                        var epson_printer = self.epson_priner_by_id[printer['printer_id'][0]];
                        if (epson_printer) {
                            var categoriers = [];
                            for (var index in printer.product_categories_ids) {
                                var category_id = printer.product_categories_ids[index];
                                var category = self.pos_category_by_id[category_id];
                                if (category) {
                                    categoriers.push(category);
                                }
                            }
                            epson_printer['categoriers'] = categoriers;
                            self.epson_priner_by_id[epson_printer['id']] = epson_printer;
                            self.epson_priner_by_ip[epson_printer['ip']] = epson_printer;
                            var epson_exsited_before = _.find(self.epson_printers, function (printer) {
                                return printer['id'] == epson_printer['id']
                            });
                            if (!epson_exsited_before) {
                                self.epson_printers.push(epson_printer)
                            }
                        }
                    }
                }
                _super_restaurant_printer_model_loaded(self, printers);
            };
            var base_pos_category_model = this.get_model('pos.category');
            var _super_pos_category_model_loaded = base_pos_category_model.loaded;
            base_pos_category_model.loaded = function (self, categories) {
                self.pos_category_by_id = {};
                for (var i = 0; i < categories.length; i++) {
                    var category = categories[i];
                    self.pos_category_by_id[category.id] = category;
                }
                _super_pos_category_model_loaded(self, categories);
            };
            _super_PosModel.initialize.apply(this, arguments);
        },
        // TODO:
        print_network: function (receipt, proxy) {
            var self = this;
            var printer = _.find(this.epson_printers, function (epson_printer) {
                return epson_printer['ip'] == proxy && epson_printer['state'] == 'Online'
            });
            if (!printer) {
                return this.gui.show_popup('dialog', {
                    title: 'Warning',
                    body: 'Printer IP ' + proxy + ' Offline, please check printer'
                })
            }
            var params = {
                receipt: receipt,
                proxy: proxy,
            };
            if (!this.proxy || !this.proxy.host) {
                return this.gui.show_popup('dialog', {
                    title: 'Error',
                    body: 'Your pos config not setting POSBOX proxy'
                })
            }
            this.proxy.connection.rpc("/hw_proxy/print_network", params, {
                shadow: true,
                timeout: 2500
            }, function (error) {
                console.error(error);
                self.pos.set('status_printer', {'state': 'disconnected', 'pending': 1});
            }).then(function (result) {
                console.log(result)
            })

        },
    });


    models.Order = models.Order.extend({
        printChanges: function () {
            var printers = this.pos.printers;
            for (var i = 0; i < printers.length; i++) {
                var printer = printers[i];
                var order = this.pos.get_order();
                order.order_in_kitchen = true;
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
                var changes = this.computeChanges(printer.config.product_categories_ids);
                changes.datetime = datetime;
                changes.date_only = date_only;
                changes.time_only = time_only;
                changes.customer_count = order['customer_count'];                
                console.log("asdfasdfffffffffffffffffffffffffffff",this);
                console.log("asdfasdfffffffffffffffffffffffffffff",changes);
                console.log("changes");
                if (changes['new'].length > 0 || changes['cancelled'].length > 0) {
                    var receipt = qweb.render('OrderChangeReceipt', {changes: changes, widget: this});
                    if (!printer.config.printer_id) {
                        printers[i].print(receipt);
                    } else {
                        var epson_printer_will_connect = this.pos.epson_priner_by_id[printer.config.printer_id[0]];
                        var epson_printer = _.find(this.pos.epson_printers, function (epson_printer) {
                            return epson_printer['ip'] == epson_printer_will_connect['ip'] && epson_printer['state'] == 'Online'
                        });
                        if (epson_printer) {
                            this.pos.print_network(receipt, epson_printer['ip'])
                        } else {
                            printers[i].print(receipt);
                        }
                    }
                }
            }
        },
    })
});