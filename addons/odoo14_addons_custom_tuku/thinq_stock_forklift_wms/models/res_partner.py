# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
import base64
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqForkliftInheritResPartner(models.Model):
    _inherit = "res.partner"

    is_operator = fields.Boolean('Operator?')
