# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class ThinqInheritStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    warehouse_id = fields.Many2one(
        'stock.warehouse', compute='_get_move_warehouse', string='Warehouse')
    ## Package/Pallet filter by warehouse_id ##
    # package_id = fields.Many2one(
    #     'stock.quant.package', 'Source Package', ondelete='restrict',
    #     check_company=True,
    #     domain="[('location_id', '=', location_id),('warehouse_owner_id', '=', warehouse_id)]")
    borrowed_status = fields.Boolean(string='Palet Dipinjam')
    #todo
    """
    1.onchange borrowd status update status available = false di stock.quant.package
    2.add query history package
    """
    start_borrowed = fields.Datetime(string='Tanggal Dipinjam')
    end_borrowed = fields.Datetime(string='Tanggal Dikembalikan')

    @api.depends('move_id', 'move_id.warehouse_id')
    def _get_move_warehouse(self):
        for move_line in self:
            move_line.warehouse_id = move_line.move_id.warehouse_id.id if move_line.move_id and move_line.move_id.warehouse_id else False
    
