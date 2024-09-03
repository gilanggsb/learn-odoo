# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2021 Thinq Technology
#    (<http://www.thinq.id>).
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
    'name': 'Warehouse Management System Inbound Fleet - Thinq 1.0',
    'version': '12.0.0.1.0',
    'author': "Thinq.id",
    'website': 'http://www.thinq.id',
    'license': 'AGPL-3',
    'category': 'Warehouse',
    'summary': 'All about inventory or warehouse inbound fleet',
    'support': 'thinqindonesia@gmail.com',
    'depends': [
        'thinq_stock_wms',
    ],
    'description': """
This module aims to improve the Inventory Process
=================================================
* inventory module customization
* etc.
""",
    'demo': [],
    'test': [],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'views/stock_inbound_fleet_view.xml',
     ],
    'css': [],
    'js': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
