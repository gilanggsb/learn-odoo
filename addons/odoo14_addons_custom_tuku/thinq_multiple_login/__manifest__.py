{
    'name': 'Thinq - Multiple Login',
    'version': '1.0',
    'description': 'Allow Partners/Employees have same user login',
    'summary': 'Allow Partners/Employees have same user login',
    'author': 'Novallingga Dirgantara',
    'website': 'https://thinq-tech.id',
    'license': 'LGPL-3',
    'category': 'custom',
    'depends': [
        'base',
        'web'
    ],
    'data': [
        'views/res_partner.xml',
        'views/res_users.xml',
        'views/partner_login.xml',
    ],
    'auto_install': False,
    'application': False
}