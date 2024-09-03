# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
import base64
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqInheritProductPackaging(models.Model):
    _inherit = "product.packaging"

    @api.model
    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
        default=lambda self: self._default_warehouse_id(), ondelete='set null')

    

class ThinqInheritQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    warehouse_owner_id = fields.Many2one('stock.warehouse', string='Warehouse Owner')

    warehouse_id = fields.Many2one(
        'stock.warehouse', compute='_get_packaging_warehouse', string='Warehouse')
    available = fields.Boolean('Available', default=True)

    @api.depends('packaging_id', 'packaging_id.warehouse_id')
    def _get_packaging_warehouse(self):
        for sqp in self:
            sqp.warehouse_id = sqp.packaging_id.warehouse_id.id if sqp.packaging_id and sqp.packaging_id.warehouse_id else False


