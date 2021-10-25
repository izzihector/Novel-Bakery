# -*- coding: utf-8 -*-
from odoo import http
import logging
import subprocess
import json
import odoo.addons.hw_proxy.controllers.main as hw_proxy
from odoo.addons.hw_escpos.escpos.printer import Network

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.hw_proxy.controllers import main as hw_proxy
    from odoo.addons.hw_escpos.controllers.main import EscposDriver
except ImportError:
    EscposDriver = object


class EscposNetworkDriver(EscposDriver):

    def print_network(self, receipt, ip, name=None):
        printer_object = Network(ip)
        printer_object.open()
        if printer_object:
            printer_object.receipt(receipt)
            printer_object.__del__()


network_driver = EscposNetworkDriver()

class NetWorkController(Network):
    def _raw(self, msg):
        _logger.info('_raw ------------ will print few seconds -----------')
        _logger.info(type(msg))
        if type(msg) is str:
            msg = msg.encode("utf-8")
        self.device.send(msg)

class UpdatedEscposProxy(hw_proxy.Proxy):

    @http.route('/hw_proxy/print_xml_receipt', type='json', auth='none', cors='*')
    def print_xml_receipt(self, receipt, proxy=None):
        _logger.info('ESCPOS: called print_xml_receipt')
        _logger.info('proxy ip: %s' % proxy)
        if proxy:
            network_driver.print_network(receipt, proxy)
        else:
            super(UpdatedEscposProxy, self).print_xml_receipt(receipt)
        return json.dumps({'state': 'succeed', 'values': {}})

    @http.route('/hw_proxy/get_printers_status', type='json', auth='none', cors='*')
    def ping_printer(self, printer_ips=[]):
        _logger.info('ESCPOS: ping proxy %s' % printer_ips)
        values = {}
        for printer_ip in printer_ips:
            _logger.info('Ping printer ip: %s' % printer_ip)
            p = subprocess.Popen(['ping', printer_ip,'-c','1',"-W","2"])
            p.wait()
            if p.poll() == 0:
                values[printer_ip] = 'Online'
            else:
                values[printer_ip] = 'Offline'
        return json.dumps({'state': 'succeed', 'values': values})
