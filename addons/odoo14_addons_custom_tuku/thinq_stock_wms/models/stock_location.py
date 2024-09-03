# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class ThinqInheritStockLocation(models.Model):
    _inherit = "stock.location"

    customer_ids = fields.Many2many('res.partner', 'customer_partner_location_rel', 'location_id', 'customer_id',
        string="Customers", copy=False)
    customer_count = fields.Integer(compute='_compute_customer_count', string="Customer Count")
    user_id = fields.Many2one('res.users', string='Responsible (PIC)', default=lambda self: self.env.user)
    product_level_ids = fields.Many2many('product.level', 'product_level_stock_location_rel', 'location_id', 'product_level_id',
        string='Product Level (Kadar)', copy=False)

    @api.depends('customer_ids')
    def _compute_customer_count(self):
        for location in self:
            location.customer_count = len(location.mapped('customer_ids')) if location.mapped('customer_ids') else 0

    def action_view_customer_list(self):
        customers = self.mapped('customer_ids')
        action = self.env.ref('base.action_partner_customer_form').read()[0]
        if len(customers) > 1:
            action['domain'] = [('id', 'in', customers.ids)]
        elif len(customers) == 1:
            form_view = [(self.env.ref('base.view_partner_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = customers.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

