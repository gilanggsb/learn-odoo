# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
import base64
import requests
import json
from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqInheritResPartner(models.Model):
    _inherit = "res.partner"

    location_ids = fields.Many2many('stock.location', 'customer_partner_location_rel', 'customer_id', 'location_id',
        string="Locations", copy=False)
    location_count = fields.Integer(
        compute='_compute_location_count', string="Location Count")
    phone = fields.Char(string='Phone Number', required=True)
    username = fields.Char(string="Username")
    password = fields.Char(string="Password")
    token = fields.Char(string="Token Login")
    product_line_ids = fields.One2many('product.template', 'customer_id',
                                       string='Customer Product List', copy=False)
    image_url = fields.Char(string='URL')
    warehouse_ids = fields.Many2many('stock.warehouse', 'customer_partner_stock_warehouse_rel', 'customer_id', 'warehouse_id',
        string="Warehouses", copy=False)
    # is_mobileappuser = fields.Boolean('Mobile App User?')
    # warehouse_id = fields.Many2one('stock.warehouse', string='PIC Warehouse Of')
    # type = fields.Selection(selection_add=[('vendor', 'Vendor Address')])
    # code = fields.Char(string="Code")

    @api.depends('location_ids')
    def _compute_location_count(self):
        for partner in self:
            partner.location_count = len(partner.mapped(
                'location_ids')) if partner.mapped('location_ids') else 0

    @api.model
    def _check_wms_credentials(self,username, password):
        """ Override this method to plug additional authentication methods"""
        res = self.search([('username','=',username),('password','=',password)])
        if not res:
            raise AccessDenied()
        return res

    def action_view_customer_location(self):
        customer_locations = self.mapped('location_ids')
        action = self.env.ref('stock.action_location_form').read()[0]
        if len(customer_locations) > 1:
            action['domain'] = [('id', 'in', customer_locations.ids)]
        elif len(customer_locations) == 1:
            form_view = [(self.env.ref('stock.view_location_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + \
                    [(state, view)
                     for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = customer_locations.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def upload_image(self):
        for rec in self:
            if not rec.name:
                raise ValidationError('Please fill in Image Name!')
            if not rec.image_medium:
                raise ValidationError('Please fill in the Image!')
            image_source = rec.image_medium
            sample_string_bytes = base64.b64decode(image_source)
            image_source = base64.b64encode(sample_string_bytes)
            url_link2 = rec.env['ir.config_parameter'].search(
                [('key', '=', 'url_img_storage')]).value
            data_user = {'partner_id': rec.id, 'image': str(image_source.decode(
                "utf-8")), 'partner_name': rec.display_name or rec.name, 'type': 'res_partner'}
            r2 = requests.post(url=url_link2, json=data_user, verify=False)
            json_user_data = r2.json()
            rec.write({'image_url': json_user_data.get('url_image')})
            if json_user_data.get('status') == 'error':
                raise ValidationError(_('%s' % json_user_data.get('message')))

class ThinqMobilePortalMenu(models.Model):
    _name = 'thinq.menu'

    name = fields.Char("Menu Name")
    module = fields.Selection([
        ('mobile', 'Mobile Apps'),
        ('portal', 'Portal'),], string="Module")

class ThinqMobilePortalAccessRight(models.Model):
    _name = 'thinq.access.right'

    name = fields.Char("Menu Name")
    menu_id = fields.Many2one('thinq.menu', string='Menu')
    can_view = fields.Boolean('Can View?')
    can_edit = fields.Boolean('Can Edit?')
    can_delete = fields.Boolean('Can Delete?')
    can_approve = fields.Boolean('Can Approve?')

class ThinqMobilePortalUserAccessRight(models.Model):
    _name = 'thinq.user.access.right'

    partner_id = fields.Many2one('res.partner', string='User')
    access_right_ids = fields.Many2many('thinq.access.right', 'thinq_access_right_user_rel', 'access_id', 'user_id', 'Access Right')