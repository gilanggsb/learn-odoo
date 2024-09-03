# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from types import resolve_bases
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqInboundFleetInheritStockPicking(models.Model):
    _inherit = "stock.picking"

    inbound_fleet_id = fields.Many2one('thinq.stock.inbound.fleet', string='Inbound Fleet')