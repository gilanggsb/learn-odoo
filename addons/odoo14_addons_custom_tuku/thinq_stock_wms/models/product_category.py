# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
import base64
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqInheritProductCategory(models.Model):
    _inherit = "product.category"
    
    image = fields.Binary(string='Category Image', attachment=True)
    image_url = fields.Char(string='URL')

    def upload_image(self):
        for rec in self:
            if not rec.name:
                raise ValidationError('Please fill in Image Name!')
            if not rec.image:
                raise ValidationError('Please fill in the Image!')
            image_source = rec.image
            sample_string_bytes = base64.b64decode(image_source)
            image_source = base64.b64encode(sample_string_bytes)
            url_link2 = rec.env['ir.config_parameter'].search([('key','=','url_img_storage')]).value
            data_user = {'category_id' : rec.id ,'image' : str(image_source.decode("utf-8")), 
                    'category_name': rec.display_name or rec.name, 'type' : 'product_category'}
            r2 = requests.post(url=url_link2, json=data_user,verify=False)
            json_user_data = r2.json()
            rec.write({'image_url': json_user_data.get('url_image')})
            if json_user_data.get('status') == 'error':
                raise ValidationError(_('%s' % json_user_data.get('message')))

