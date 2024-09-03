# -*- encoding: utf-8 -*-
# © 2021 Thinq Technology
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class ThinqWzdActivateExpiredProduct(models.TransientModel):
    _name = 'wzd.activate.expired.product'

    @api.model
    def _default_product_id(self):
        active_model = self._context.get('active_model')
        if active_model == 'product.product':
            return self._get_active_id()
        return None

    product_id = fields.Many2one(comodel_name='product.product', string='Product', default=_default_product_id)
    
    expired_date = fields.Date(string='Expiration Date', default=lambda self:
        self.env['product.product'].compute_next_year_date(fields.Date.context_today(self)))
    expiration_reminder_days = fields.Integer(string='Expiration Reminder Day(s)')

    @api.model
    def _get_active_id(self):
        return self.env[self._context.get('active_model')].browse(
            self._context.get('active_id')
        )

    def action_activate_product(self):
        vals = {
            'expired_date': self.expired_date, 
            'expiration_reminder_days': self.expiration_reminder_days,
            'active': True
        }        
        self.product_id.write(vals)
        self.product_id.message_post(cr=self._cr, uid=self._uid,
                body="This product has been reactivated. ", context=None)

