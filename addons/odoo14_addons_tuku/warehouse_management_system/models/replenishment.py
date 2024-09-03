# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict
from datetime import datetime, time
from datetime import timedelta, date
from dateutil import relativedelta
from itertools import groupby
from json import dumps
from psycopg2 import OperationalError

import base64
import io

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import add, float_compare, float_round, float_is_zero, frozendict, split_every, format_datetime
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class Replenishment(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    qty_buffer = fields.Float('Buffer Quantity')

    # @api.depends('qty_multiple', 'qty_forecast', 'product_min_qty', 'product_max_qty', 'qty_buffer')
    # def _compute_qty_to_order(self):
    #     for orderpoint in self:
    #         if not orderpoint.product_id or not orderpoint.location_id:
    #             orderpoint.qty_to_order = False
    #             continue
    #         qty_to_order = 0.0
    #         rounding = orderpoint.product_uom.rounding
    #         if float_compare(orderpoint.qty_forecast, orderpoint.product_min_qty, precision_rounding=rounding) < 0:
    #             qty_to_order = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - orderpoint.qty_forecast

    #             remainder = orderpoint.qty_multiple > 0 and qty_to_order % orderpoint.qty_multiple or 0.0
    #             if float_compare(remainder, 0.0, precision_rounding=rounding) > 0:
    #                 qty_to_order += orderpoint.qty_multiple - remainder
    #         orderpoint.qty_to_order = qty_to_order

    # def action_send_stock_minimum(self):
    #     rules = self.env['stock.warehouse.orderpoint'].search([('product_min_qty','>',0)])
    #     n = 0
    #     for res in rules:
    #         if res.qty_on_hand <= res.product_min_qty:
    #             print("sending email")
    #             template_id = self.env.ref('warehouse_management_system.replenishment_email_template').id
    #             self.env['mail.template'].browse(template_id).send_mail(res.id, force_send=True)

    #             n += 1
    
    def send_email_with_excel_attach(self):
        today = date.today()
        report = self.env.ref('warehouse_management_system.action_report_xlsx')
        
        filename = 'Minimum Stock Report %s.xls' % (today)
        data = {
            'date_report': today,
            'filename':filename
        }
            
        generated_report = report._render_xlsx(self, data)
        data_record = base64.b64encode(generated_report[0])
        ir_values = {
            'name': 'Stock Minimum Report',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'stock.warehouse.orderpoint',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        email_template = self.env.ref('warehouse_management_system.replenishment_email_template')
        # if email_template:
        #     email_values = {
        #         # 'email_to': 'adefaisal.iwp17@gmail.com',
        #         'email_from': 'report@casentosa.com',
        #     }
        email_template.attachment_ids = [(4, attachment.id)]
        # email_template.send_mail(self.id, email_values=email_values)
        email_template.send_mail(self.id, force_send=True)
        email_template.attachment_ids = [(5, 0, 0)]