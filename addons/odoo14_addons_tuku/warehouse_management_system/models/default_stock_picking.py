# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date


class Picking(models.Model):
    _inherit = "stock.picking"
    _description = "Transfer"
    _order = "priority desc, scheduled_date asc, id desc"

    def _check_backorder(self):
        prec = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        backorder_pickings = self.browse()
        for picking in self:
            quantity_todo = {}
            quantity_done = {}
            for move in picking.mapped('move_lines').filtered(lambda m: m.state != "cancel"):
                quantity_todo.setdefault(move.product_id.id, 0)
                quantity_done.setdefault(move.product_id.id, 0)
                quantity_todo[move.product_id.id] += move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id, move.product_id, rounding_method='HALF-UP')
                quantity_done[move.product_id.id] += move.product_uom._compute_quantity(move.quantity_done, move.product_id.uom_id, move.product_id, rounding_method='HALF-UP')
            # FIXME: the next block doesn't seem nor should be used.
            for ops in picking.mapped('move_line_ids').filtered(lambda x: x.package_id and not x.product_id and not x.move_id):
                for quant in ops.package_id.quant_ids:
                    quantity_done.setdefault(quant.product_id.id, 0)
                    quantity_done[quant.product_id.id] += quant.qty
            for pack in picking.mapped('move_line_ids').filtered(lambda x: x.product_id and not x.move_id):
                quantity_done.setdefault(pack.product_id.id, 0)
                quantity_done[pack.product_id.id] += pack.product_uom_id._compute_quantity(pack.qty_done, pack.product_id.uom_id, pack.product_id)
            if any(
                float_compare(quantity_done[x], quantity_todo.get(x, 0), precision_digits=prec,) == -1
                for x in quantity_done
            ):
                backorder_pickings |= picking
        return backorder_pickings