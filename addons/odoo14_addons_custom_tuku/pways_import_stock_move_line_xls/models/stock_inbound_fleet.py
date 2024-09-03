# -*- coding: utf-8 -*-
from odoo import models

class StockInboundFleet(models.Model):
    _inherit = "thinq.stock.inbound.fleet"

    def action_inbound_fleet_import(self):
        action = self.env.ref('pways_import_stock_move_line_xls.action_stock_inbound_fleet_wizard').read()[0]
        action.update({'views': [[False, 'form']]})
        return action