# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class ImageFileStorage(models.Model):
    _name= 'image.file.storage'

    name = fields.Char('Name')
    image_name = fields.Char('Image Name')
    description = fields.Text('Description')
    state = fields.Selection([('draft','Draft'),('post','Post')],string="State", default="draft")
    created_by = fields.Many2one('res.users',string="Created By",track_visibility = 'onchange', default=lambda self: self.env.user)
    image = fields.Binary("Photo", attachment=True,
            help="This field holds the image used as photo for the customer/partner, limited to 1024x1024px.")

    def action_post(self):
        for record in self:
            record.write({'state':'post'})

    def action_set_to_draft(self):
        for record in self:
            record.write({'state':'draft'})
