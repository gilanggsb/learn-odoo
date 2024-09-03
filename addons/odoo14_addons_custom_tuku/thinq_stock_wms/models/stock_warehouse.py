# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class ThinqInheritStockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    customer_ids = fields.Many2many('res.partner', 'customer_partner_stock_warehouse_rel', 'warehouse_id', 'customer_id',
        string="Customers", copy=False)

    