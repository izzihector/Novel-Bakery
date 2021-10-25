# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
from odoo.exceptions import UserError

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
import logging

_logger = logging.getLogger(__name__)


class PosIoT(models.Model):
    _inherit = "pos.iot"

    def test_login(self):
        for session in self:
            if session.screen_kitchen:
                xmlrpc_url = '%s/xmlrpc/2/' % session.odoo_public_proxy
                xmlrpc_common = xmlrpclib.ServerProxy(xmlrpc_url + 'common')
                uid = xmlrpc_common.login(session.database, session.login_kitchen, session.password_kitchen)
                if uid:
                    raise UserError('Succeed Login')
                else:
                    raise UserError('Fail Login')
