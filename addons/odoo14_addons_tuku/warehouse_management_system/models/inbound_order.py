# -*- coding: utf-8 -*-
# © 2023 CAS Development

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    type = fields.Selection([('procurement',"Procurement"),('non_procurement',"Non Procurement")],default="procurement", string="Procurement Type")

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    order_type = fields.Selection([('procurement',"Procurement"),('non_procurement',"Non Procurement")], string="Order Type")