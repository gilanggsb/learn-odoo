from odoo import _, api, fields, models
from odoo.http import request

class ResPartner(models.Model):
    _inherit = 'res.partner'

    session_id = fields.Char('Session ID', readonly=True)
    user_id = fields.Many2one('res.users', string='Related User')
    access_key = fields.Char('Access Key (Password)')
