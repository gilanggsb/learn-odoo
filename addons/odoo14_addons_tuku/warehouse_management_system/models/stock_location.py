# -*- coding: utf-8 -*-
# © 2023 CAS Development

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class Location(models.Model):
    _inherit = "stock.location"
    _description = "Stock Location"

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.barcode = self.name