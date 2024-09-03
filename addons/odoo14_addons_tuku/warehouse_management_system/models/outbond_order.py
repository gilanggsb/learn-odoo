# -*- coding: utf-8 -*-
# © 2023 CAS Development

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class SalesOrder(models.Model):
    _inherit = "sale.order"

    type = fields.Selection([('sales',"Sales"),('non_sales',"Non Sales")],default="sales", string="Sales Type")

class PurchaseOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_type = fields.Selection([('sales',"Sales"),('non_sales',"Non Sales")], string="Order Type")