# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
import datetime
_logger = logging.getLogger(__name__)


class ThinqInheritStockMove(models.Model):
    _inherit = "stock.move"

    time_spend_timer = fields.Char(string='Aging', compute='_spend_timer')

    def _spend_timer(self):
        for val in self:
            if val.date:
                val.time_spend_timer = str(datetime.datetime.now() - val.date).split('.', 2)[0]