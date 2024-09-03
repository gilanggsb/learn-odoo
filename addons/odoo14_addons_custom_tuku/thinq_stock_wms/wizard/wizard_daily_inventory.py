from email.policy import default
from odoo import models, fields, api
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime ,date , timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.addons import decimal_precision as dp
import base64
import json
import xlrd
import re
import os
import csv
import itertools
from io import StringIO
class WizardDailyInventory(models.TransientModel):
    _name = 'wiz.daily.inventory'

    date_from = fields.Date(string='Date From', default=fields.Date.context_today, required=True)
    date_to = fields.Date(string='Date To', default=fields.Date.context_today, required=True)

    @api.constrains('date_from', 'date_to')
    def _onchange_(self):
        if self.date_to < self.date_from:
            raise ValidationError('Cannot Input backdate')

    def generate_report(self):
        for item in self:
            data = {
                'ids': item.ids,
                'model': item._name,
                'data': self.read()[0],
                'form' : {
                    'date_from_str' : self.date_from.strftime("%d/%m/%Y"),
                    'date_to_str' : self.date_to.strftime("%d/%m/%Y")
                }
            }
            return self.env.ref('thinq_stock_wms.action_report_daily_inventory').report_action(self,data=data)