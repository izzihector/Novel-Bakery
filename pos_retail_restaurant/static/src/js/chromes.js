odoo.define('pos_restaurant_kitchen.chrome', function (require) {
    "use strict";
    var chrome = require('point_of_sale.chrome');

    chrome.Chrome.include({
        build_widgets: function () {
            this._super();
            if (this.pos.config.screen_type && (this.pos.config.screen_type == 'kitchen' || this.pos.config.screen_type == 'kitchen_waiter')) {
                this.gui.set_startup_screen('kitchen_screen');
                this.gui.set_default_screen('kitchen_screen');
                setTimeout(function () {
                    $('.debug-widget').addClass('oe_hidden');
                }, 500)
            }
        }
    });

    chrome.OrderSelectorWidget.include({
        renderElement: function () {
            this._super();
            var orders = this.pos.get('orders').models;
            for (var i = 0; i < orders.length; i++) {
                var has_line_waitinng_delivery = orders[i].get_lines_need_delivery();
                if (has_line_waitinng_delivery) {
                    var $order_content = $("[data-uid='" + orders[i].uid + "']");
                    $order_content.addClass('order-waiting-delivery');
                } else {
                    var $order_content = $("[data-uid='" + orders[i].uid + "']");
                    $order_content.removeClass('order-waiting-delivery');
                }
            }
        }
    });

    var screens = require('point_of_sale.screens');
    screens.ScreenWidget.include({
        show: function () {
            this._super();
            var config = this.pos.config;
            if (config.screen_type && (config.screen_type == 'kitchen' || config.screen_type == 'kitchen_waiter')) {
                $('.pos').addClass('kitchen');
                $('.screen').addClass('kitchen');
                $('.oe_status').addClass('oe_hidden');
                $('.refresh_screen_widget').removeClass('oe_hidden');
                $('.js_sync_status').removeClass('oe_hidden')
            }
        },
        renderElement: function () {
            this._super();
            var config = this.pos.config;
            if (config.screen_type && (config.screen_type == 'kitchen' || config.screen_type == 'kitchen_waiter')) {
                $('.full-content').css("top", '0px');
            }
        }
    });

});
