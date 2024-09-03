# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ProductLevel(models.Model):
    _name = 'product.level'

    name = fields.Char('Type', required=True, translate=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Level name already exists !"),
    ]

