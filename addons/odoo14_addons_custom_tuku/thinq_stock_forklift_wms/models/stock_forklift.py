# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from types import resolve_bases
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class StockForklift(models.Model):
    _name = "thinq.stock.forklift"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forklift"
    _order = "name asc"

    name = fields.Char(string='Forklift Name')
    code = fields.Char(string='Forklift Code')
    partner_id = fields.Many2one('res.partner', string='Operator', domain="[('is_operator', '=', True)]")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')