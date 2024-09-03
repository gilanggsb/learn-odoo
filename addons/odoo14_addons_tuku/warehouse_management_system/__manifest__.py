# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2021 CAS Development
#    (<http://www.casentosa.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Warehouse Management System - CAS',
    'version': '14.0.0.1',
    'author': "CAS",
    'website': 'http://www.casentosa.com',
    'license': 'AGPL-3',
    'category': 'Warehouse',
    'summary': 'All about order planning',
    'support': 'support@casentosa.com',
    'depends': [
        'account','purchase','sale_stock','stock','product','mrp','stock_account','stock_3dbase','uom','report_xlsx',
    ],
    'description': """
This module is all about warehouse management system by CAS
=================================================
* Inbound Module Customization
* Outbound Module Customization
* Manufacturing Module Customization
* etc.
""",
    'demo': [],
    'test': [],
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'wizard/minimum_stock_report_wizard.xml',
        'views/inbound_view.xml',
        'views/outbond_view.xml',
        'views/mrp_production_batch_view.xml',
        'views/wms_menu_view.xml',
        'views/stock_location_view.xml',
        'views/product_view.xml',
        'views/res_partner_view.xml',
        'views/lot_serial_view.xml',
        'views/replenishment_view.xml',
        'reports/replenishment_mail.xml',
        'reports/minimum_stock_report.xml',
     ],
    'css': [],
    'js': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}