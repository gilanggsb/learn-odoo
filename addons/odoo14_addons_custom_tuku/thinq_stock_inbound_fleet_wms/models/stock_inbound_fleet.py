# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from types import resolve_bases
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
_logger = logging.getLogger(__name__)


class StockInboundFleet(models.Model):
    _name = "thinq.stock.inbound.fleet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Inbound Fleet"
    _order = "name asc"

    name = fields.Char(string='Nopol Kendaraan')
    date_in = fields.Datetime(string='Tanggal & Waktu Datang')
    partner_id = fields.Many2one('res.partner', string='Customer', domain="[('customer_rank', '>', '0')]")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    cust_po_no = fields.Char(string='Customer PO No')
    netto_tonase = fields.Float(string='Netto')
    bruto_tonase = fields.Float(string='Bruto')
    inbound_line_ids = fields.One2many('thinq.stock.inbound.fleet.line', 'inbound_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft')
    time_spend_timer = fields.Char(string='Durasi Timer', compute='_spend_timer')
    time_spend_actual = fields.Char(string='Durasi')
    date_confirm_compute = fields.Datetime(string='Tanggal Confirm', compute='_compute_date_confirm')
    date_confirm = fields.Datetime(string='Tanggal Confirm')
    is_inbound = fields.Boolean(string='Is Inbound')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    def _compute_date_confirm(self):
        for val in self:
            val.date_confirm_compute = datetime.datetime.now()
            if val.date_confirm:
                val.date_confirm_compute = val.date_confirm
            picking_ids = self.env['stock.picking'].search([('inbound_fleet_id', '=', val.id)])
            if len(picking_ids):
                picking_id = picking_ids[0]
                val.date_confirm_compute = picking_id.create_date

    def _spend_timer(self):
        for val in self:
            if val.date_confirm_compute:
                val.time_spend_timer = str(datetime.datetime.now() - val.date_confirm_compute).split('.', 2)[0]

    def create_stock_picking(self):
        customer_location_ids = self.env['stock.location'].search([('usage', '=', 'customer')])
        if len(customer_location_ids) > 0:
            customer_location_id = customer_location_ids[0]

        supplier_location_ids = self.env['stock.location'].search([('usage', '=', 'supplier')])
        if len(supplier_location_ids) > 0:
            supplier_location_id = supplier_location_ids[0]

        partner_id = self.partner_id
        warehouse_id = self.warehouse_id
        picking_id = False
        new_stock_picking = None
        if self.is_inbound:
            picking_type_id = warehouse_id.in_type_id
            default_location_dest_id = picking_type_id.default_location_dest_id
            new_stock_picking = self.env['stock.picking'].create({
                    'partner_id': partner_id.id,
                    'picking_type_id': picking_type_id.id,
                    'location_id' : customer_location_id.id,
                    'location_dest_id' : default_location_dest_id.id,
                    'inbound_fleet_id' : self.id
            })
            picking_id = new_stock_picking.id
            for line in self.inbound_line_ids:
                new_stock_move = self.env['stock.move'].create({
                    'picking_id': picking_id,
                    'product_id': line.product_id.id,
                    'name' : line.product_id.name,
                    'product_uom_qty' : line.product_qty,
                    'product_uom' : line.product_uom_id.id,
                    'location_id' : customer_location_id.id,
                    'location_dest_id' : default_location_dest_id.id
                })
            
            if picking_id:
                self.picking_id = picking_id
                self.state = 'confirmed'
                self.date_confirm = datetime.datetime.now()
                new_stock_picking.action_confirm()
        else:
            so = self.env['sale.order'].create({
                'partner_id': partner_id.id,
                'warehouse_id' : warehouse_id.id
            })
            if so:
                for line in self.inbound_line_ids:
                    sol = self.env['sale.order.line'].create({
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_qty,
                        'product_uom': line.product_uom_id.id,
                        'price_unit': 1,
                        'order_id': so.id
                    })
                so.action_confirm()
                for picking in so.picking_ids:
                    picking.origin = so.name
                    new_stock_picking = picking
                    picking_id = picking.id
                    picking.inbound_fleet_id = self.id 

                if picking_id:
                    self.picking_id = picking_id
                    self.state = 'confirmed'
                    self.date_confirm = datetime.datetime.now()
                    new_stock_picking.action_confirm()


    def cancel(self):
        self.state = 'cancel'

    #API
    @api.model
    def create_inbound(self, params):
        partner_id = params.get('partner_id')
        warehouse_id = params.get('warehouse_id')
        cust_po_no = params.get('cust_po_no')
        name = params.get('no_pol')
        is_inbound = params.get('is_inbound')
        state = 'draft'
        new_inbound = self.env['thinq.stock.inbound.fleet'].create({
                'partner_id': partner_id,
                'warehouse_id': warehouse_id,
                'cust_po_no' : cust_po_no,
                'name' : name,
                'state' : state,
                'is_inbound' : is_inbound
        })
        inbound_id = new_inbound.id
        result = []
        if inbound_id:
            result.append({
                "status" : 'success',
                "inbound_id": inbound_id,
            })
        else:
            result.append({
                "status" : 'error'
            })
        return result

    @api.model
    def create_inbound_line(self, params):
        result = []
        val_id = params.get('id')
        inbound_id = params.get('inbound_id')
        product_id = params.get('product_id')
        product_uom_id = params.get('product_uom_id') 
        product_qty = params.get('product_qty')
        
        # edit
        if val_id:
            stock_picking_line = self.env['thinq.stock.inbound.fleet.line'].browse(val_id)
            if stock_picking_line:
                stock_picking_line.product_id = product_id
                stock_picking_line.product_uom_id = product_uom_id
                stock_picking_line.product_qty = product_qty
                result.append({
                    "status": 'success',
                    "inbound_line_id" : val_id
                })
            else:
                result.append({
                    "status": 'error',
                })
            return result
        else:
            new_stock_picking_line = self.env['thinq.stock.inbound.fleet.line'].create({
                    'inbound_id': inbound_id,
                    'product_id': product_id,
                    'product_uom_id' : product_uom_id,
                    'product_qty' : product_qty
            })
            inbound_line_id = new_stock_picking_line.id
            if inbound_line_id:
                result.append({
                    "status": 'success',
                    "inbound_line_id" : inbound_line_id
                })
            else:
                result.append({
                    "status": 'error',
                })
            return result

    @api.model
    def confirm_inbound(self, params):
        inbound_id = self.browse(params.get('inbound_id'))
        result = []
        if inbound_id:
            inbound_id.create_stock_picking()
            result.append({
                "status" : 'success',
                "inbound_id": inbound_id,
            })
        else:
            result.append({
                "status" : 'error'
            })
        return result

    @api.model
    def get_list_inbound_fleet(self, params):
        data = []
        result = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = []
        try:
            
            dom += [('is_inbound','=',params.get('is_inbound'))]
            
            if params.get('state'):
                dom += [('state','=',params.get('state'))]
            else:
                dom += [('state','=','draft')]

            if params.get('inbound_id'):
                dom = [('id', '=', params.get('inbound_id'))]
                
            inbounds = self.search(dom,order="id desc",offset=offset,limit=limit)
            total_data = self.search_count(dom)
            
            if inbounds:
                for p in inbounds:
                    result_line = []
                    # if params.get('inbound_id'):
                    for line in p.inbound_line_ids:
                        val_line = {
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name if line.product_id else '',
                            "product_uom_id": line.product_uom_id.id,
                            "product_uom_id_name": line.product_uom_id.name if line.product_uom_id else '',
                            "product_qty": line.product_qty
                        }
                        result_line.append(val_line)
                    data.append({
                        "id": p.id,
                        "total_data":total_data,
                        "name": p.name,
                        "date_in" : p.date_in,
                        "customer_id" : p.partner_id.id if p.partner_id else '',
                        "customer_name" : p.partner_id.name if p.partner_id else '',
                        "customer_po_no" : p.cust_po_no,
                        "warehouse_id" : p.warehouse_id.id if p.warehouse_id else '',
                        "warehouse_name" : p.warehouse_id.name if p.warehouse_id else '',
                        "state" : p.state,
                        "line_ids": result_line
                    })
            result.append({
                "data" : data,
                "total_data" : total_data
            })
            return result
        except Exception as e:
                ValidationError(e)

class StockInboundFleetLine(models.Model):
    _name = "thinq.stock.inbound.fleet.line"
    _description = "Product"
    _rec_name = "product_id"
    _order = "id"

    inbound_id = fields.Many2one('thinq.stock.inbound.fleet', 'Inbound Fleet', index=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True, domain="[('type', '!=', 'service')]")
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_qty = fields.Float('Quantity', digits=0)
    name = fields.Char(string='Name', related='product_id.name')