from odoo import http
from odoo.addons.web.controllers.main import Home
from odoo.http import request


class Home(Home):

    def _login_redirect(self, uid, redirect=None):
        user_id = request.env['res.users'].sudo().browse(uid)
        if user_id.is_multiple_login:
            redirect = '/web/partner/login'
        return super(Home, self)._login_redirect(uid, redirect=redirect)

    @http.route('/web/partner/login', type='http', auth="none")
    def web_partner_login(self, **kw):
        print('PARAMSSSS', kw)
        values = {}
        if request.httprequest.method == 'POST':
            partner_id = request.env['res.partner'].sudo().search([('access_key','=',kw.get('access_key'))])
            if partner_id:
                partner_id.sudo().write({'session_id': request.session.session_token})
                return http.redirect_with_hash('/web')
            else:
                values['error'] = 'Wrong Access Key!'
        return request.render('thinq_multiple_login.partner_login', values)
