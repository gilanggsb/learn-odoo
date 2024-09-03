from odoo import _, api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    partner_ids = fields.One2many('res.partner', 'user_id', string='Partner List in this User')
    is_multiple_login = fields.Boolean('Allow Multiple Login?')