# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class pos_config(models.Model):
    _inherit = "pos.config"

    floor_ids = fields.Many2many(
        'restaurant.floor',
        'pos_config_restaurant_floor_rel',
        'pos_config_id',
        'floor_id',
        string="Floors")
    screen_type = fields.Selection([
        ('waiter', 'Order Waiter'),
        ('kitchen_waiter', 'Kitchen Waiter'),
        ('kitchen', 'Chef/Kitchen/Bar'),
    ], string='Screen Type Session',
        default='waiter',
        help='1. Order Waiter: Is person ordering products from customers and send to Chef/Kitchen\n'
             '2. Kitchen Waiter: Is person delivery products from Chef/Kitchen Room to Customers\n'
             '3. Kitchen: is Kitchen/Bar Room\n')
    play_sound = fields.Boolean('Sound', help='Sound notify when new transaction coming')
    display_table = fields.Boolean(
        'Display Tables',
        help='Display Tables on Kitchen/bar screen',
        default=1)

    display_all_product = fields.Boolean(
        'Display all Products',
        default=1)
    product_categ_ids = fields.Many2many(
        'pos.category',
        'config_pos_category_rel',
        'config_id', 'categ_id',
        string='Categories Display',
        help='Categories of product will display on kitchen/bar screen')
    send_order_to_kitchen = fields.Boolean(
        'Send order to Kitchen',
        default=1,
        help='Check if need waiters/cashiers send order information to kitchen/bar room')
    kitchen_receipt = fields.Boolean(
        'Print Kitchen/Bar Bill',
        help='If your business not use IoT/POS Boxes, You can active it for print kitchen/bar bill viva pos web',
        default=1)
    set_lines_to_done = fields.Boolean(
        'Allow Set Lines to Done', default=1)
