# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_send_expiration_reminder = fields.Boolean("Product Expiration Reminder", 
        implied_group='thinq_stock_wms.group_send_expiration_reminder', default=True)

