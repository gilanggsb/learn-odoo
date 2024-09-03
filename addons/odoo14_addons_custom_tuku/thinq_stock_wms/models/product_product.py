# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
import base64
import requests
import json
import re
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import ormcache, formataddr
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class ThinqInheritProductTemplate(models.Model):
    _inherit = "product.template"

    sku_number = fields.Char('SKU Number', compute='_compute_sku_number',
        inverse='_set_sku_number', store=True)
    customer_id = fields.Many2one('res.partner', string='Customer', index=True, ondelete='cascade')
    image_url = fields.Char(string='URL')
    level_id = fields.Many2one('product.level', string='Level', ondelete='set null')

    @api.depends('product_variant_ids', 'product_variant_ids.sku_number')
    def _compute_sku_number(self):
        unique_variants = self.filtered(lambda tmpl: len(tmpl.product_variant_ids) == 1)
        for tmpl in unique_variants:
            tmpl.sku_number = tmpl.product_variant_ids.sku_number
        for tmpl in (self - unique_variants):
            tmpl.sku_number = False

    def _set_sku_number(self):
        for tmpl in self:
            if len(tmpl.product_variant_ids) == 1:
                tmpl.product_variant_ids.sku_number = tmpl.sku_number

    @api.model_create_multi
    def create(self, vals_list):
        product_tmpl = super(ThinqInheritProductTemplate, self).create(vals_list)
        for tmpl, vals in zip(product_tmpl, vals_list):
            related_vals = {}
            if vals.get('sku_number'):
                related_vals['sku_number'] = vals['sku_number']
            if related_vals:
                tmpl.write(related_vals)
        return product_tmpl
    
    @api.depends('name', 'default_code', 'sku_number')
    def name_get(self):
        res = []
        for rec in self:
            name = '%s' % rec.name
            if rec.default_code and rec.sku_number:
                name = '%s%s' % (rec.default_code and '[%s | %s] ' % (rec.default_code, rec.sku_number), name)
            elif not rec.default_code and rec.sku_number:
                name = '%s%s' % (rec.sku_number and '[%s] ' % rec.sku_number, name)
            elif rec.default_code and not rec.sku_number:
                name = '%s%s' % (rec.default_code and '[%s] ' % rec.default_code, name)
            res.append((rec.id, name))
        return res

    def upload_image(self):
        for item in self:
            if not item.name:
                raise ValidationError('Please fill in Image Name!')
            if not item.image_1920:
                raise ValidationError('Please fill in the Image!')
            image_source = item.image_1920
            sample_string_bytes = base64.b64decode(image_source)
            image_source = base64.b64encode(sample_string_bytes)
            url_link2 = item.env['ir.config_parameter'].search([('key','=','url_img_storage')]).value
            if not url_link2:
                url_link2 = 'https://cas-wms-odoo-dev-local.tech-lab.space/'
            data_user = {'product_id' : item.id ,'image' : str(image_source.decode("utf-8")) , 'product_name' : item.name , 'type' : 'product_template'}
            data_json = json.dumps(data_user)
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url=url_link2, headers=headers, json=data_json,verify=False)
                # response.raise_for_status()
            except requests.exceptions.Timeout:
                raise UserError(_('Timeout occurred while trying to upload image.'))
            except Exception as e:
                _logger.exception("Error when uploading image: %s" % e)
                raise UserError(_('Uploading images cannot be done, please try again later.'))
            res = json.loads(response.content)
            _logger.info("upload_image: Received response:\n%s\n%s" % (res, response.text))
            json_user_data = response.json()
            item.write({'image_url': json_user_data.get('url_image')})
            if json_user_data.get('status') == 'error':
                raise ValidationError(_('%s' % json_user_data.get('message')))
            for rec in item.product_variant_ids:
                if not rec.image_url:
                    rec.write({'image_url': json_user_data.get('url_image')})



class ThinqInheritProductProduct(models.Model):
    _inherit = "product.product"
    _order = 'sku_number, default_code, name, id'

    def compute_next_year_date(self, strdate):
        oneyear = relativedelta(years=5)
        start_date = fields.Date.from_string(strdate)
        return fields.Date.to_string(start_date + oneyear)

    sku_number = fields.Char(string="SKU Number", index=True)
    expired_date = fields.Date(string='Product Expiration Date', default=lambda self:
        self.compute_next_year_date(fields.Date.context_today(self)), 
        help='Product Expiration Date (by default, five year after begin date)')
    expiration_reminder_days = fields.Integer(string='Expiration Reminder Day(s)',
        help='Number of days reminder expiration')
    expire_days_left = fields.Integer(compute='_compute_expire_days_left', string='Expiration days remaining')
    image_url = fields.Char(string='URL')
    mul_max_stock = fields.Float('Multiple Maximum Stock')
    mul_min_stock = fields.Float('Multiple Minimum Stock')
    delivery_time = fields.Float('Delivery Time')
    daily_usage = fields.Float('Daily Usage')
    max_stock = fields.Float('Maximum Stock')
    min_stock = fields.Float('Minimum Stock')

    _sql_constraints = [
        ('sku_number_company_uniq', 'unique (sku_number, company_id)', 'SKU Number must be unique per company !')
    ]

    def name_get(self):
        # TDE: this could be cleaned a bit I think
        def _name_get(d):
            name = d.get('name', '')
            product_code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            product_sku_no = self._context.get('display_sku_number', True) and d.get('sku_number', False) or False
            if product_code and product_sku_no:
                name = '[%s | %s] %s' % (product_code,product_sku_no,name)
            elif product_code and not product_sku_no:
                name = '[%s] %s' % (product_code,name)
            elif not product_code and product_sku_no:
                name = '[%s] %s' % (product_sku_no,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'sku_number'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              'sku_number': product.sku_number,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          'sku_number': product.sku_number,
                          }
                result.append(_name_get(mydict))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(self._search(['|',('sku_number', '=', name),('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + ['|',('sku_number', operator, name),('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('sku_number', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                    ['&', ('sku_number', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search(['|',('sku_number', '=', res.group(2)),('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return product_ids

    @api.depends('expired_date')
    def _compute_expire_days_left(self):
        for record in self:
            if record.expired_date:
                today = fields.Date.from_string(fields.Date.today())
                renew_date = fields.Date.from_string(record.expired_date)
                diff_time = (renew_date - today).days
                record.expire_days_left = diff_time > 0 and diff_time or 0
            else:
                record.expire_days_left = -1

    def _send_expiration_reminder_mail(self, send_single=False):
        if not self.user_has_groups('thinq_stock_wms.group_send_expiration_reminder'):
            return

        template = self.env.ref('thinq_stock_wms.email_template_product_expires_soon_reminder', raise_if_not_found=False)
        template2 = self.env.ref('thinq_stock_wms.email_template_product_expired_reminder', raise_if_not_found=False)
        if template or template2:
            product_list = self if send_single else self._get_products_to_remind()
            for product in product_list:
                if product.expired_date:
                    superuser = self.env['res.users'].sudo().browse(SUPERUSER_ID)
                    mail_sudo = self.env['mail.mail'].sudo()
                    current_date_str = fields.Date.context_today(product)
                    current_date = fields.Date.from_string(current_date_str)
                    due_time_str = product.expired_date
                    due_time = fields.Date.from_string(due_time_str)
                    diff_time = (due_time - current_date).days
                    exp_reminder_days = product.expiration_reminder_days or 30  #30 days before reminder
                    product_full_name = product.display_name or product.name_get()[0][1]
                    email_from = self.env.user.email_formatted or superuser.partner_id.email_formatted
                    email_to = '%s' % ','.join(set([formataddr((product.create_uid.partner_id.name, product.create_uid.partner_id.email)),
                                                formataddr((product.activity_user_id.partner_id.name, product.activity_user_id.partner_id.email))]))
                    ref = '%s' % ','.join([str(product._name), str(product.id)])
                    if exp_reminder_days and (diff_time < exp_reminder_days and diff_time >= 0): #product will expire soon
                        #Post on document
                        product.with_context(is_reminder=True, force_send=True).message_post_with_template(
                            template.id, email_layout_xmlid="mail.mail_notification_light", composition_mode='comment')
                        #Send email
                        body_msg = _(
                            "Product '%s' will expire soon, check or update the expiration date immediately.") % (product_full_name,)
                        mail_sudo.create({
                            'email_from': email_from,
                            'author_id': self.env.user.partner_id.id,
                            'body_html': body_msg,
                            'subject': _('Product will expire soon - %s.', product_full_name),
                            'email_to': email_to,
                            'auto_delete': True,
                            'references': ref,
                        }).send()
                    
                    if diff_time < 0 and template2: #product has expired
                        #Post on document
                        product.with_context(is_reminder=True, force_send=True).message_post_with_template(
                            template2.id, email_layout_xmlid="mail.mail_notification_paynow", composition_mode='comment')
                        #Send email
                        body_msg = _(
                            "The product '%s' has expired, product status is inactive.") % (product_full_name,)
                        mail_sudo.create({
                            'email_from': email_from,
                            'author_id': self.env.user.partner_id.id,
                            'body_html': body_msg,
                            'subject': _('Product has expired - %s.', product_full_name),
                            'email_to': email_to,
                            'auto_delete': True,
                            'references': ref,
                        }).send()
                        product._unlink_or_archive() #Auto change product is not active

    @api.model
    def _get_products_to_remind(self):
        return self.search([
            ('active', '=', True), ('expire_days_left', '<=', 0)
        ]).filtered(lambda p: bool(p.expired_date))

    def action_activate_expired_product(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Provide an expiration date to reactivate the product.",
            "target": "new",
            "src_model": "product.product",
            "res_model": "wzd.activate.expired.product",
            "view_mode": "form",
            "view_type": "form",
            "context": {
                "active_id": self.id,
            },
        }

    def upload_image(self):
        for rec in self:
            if not rec.name:
                raise ValidationError('Please fill in Image Name!')
            if not rec.image_1920:
                raise ValidationError('Please fill in the Image!')
            image_source = rec.image_1920
            sample_string_bytes = base64.b64decode(image_source)
            image_source = base64.b64encode(sample_string_bytes)
            url_link2 = rec.env['ir.config_parameter'].search([('key','=','url_img_storage')]).value
            if not url_link2:
                url_link2 = 'https://cas-wms-odoo-dev-local.tech-lab.space/'
            data_user = {'product_id' : rec.id ,'image' : str(image_source.decode("utf-8")), 'product_name': rec.display_name or rec.name, 'type' : 'product_product'}
            data_json = json.dumps(data_user)
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url=url_link2, headers=headers, json=data_json,verify=False)
                # response.raise_for_status()
            except requests.exceptions.Timeout:
                raise UserError(_('Timeout occurred while trying to upload image.'))
            except Exception as e:
                _logger.exception("Error when uploading image: %s" % e)
                raise UserError(_('Uploading images cannot be done, please try again later.'))
            res = json.loads(response.content)
            _logger.info("upload_image: Received response:\n%s\n%s" % (res, response.text))
            json_user_data = response.json()
            rec.write({'image_url': json_user_data.get('url_image')})
            if json_user_data.get('status') == 'error':
                raise ValidationError(_('%s' % json_user_data.get('message')))


