# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

SIZE_BACK_ORDER_NUMERING = 3

class MrpProductionBatch(models.Model):
    """ Production Orders Batch """
    _name = 'mrp.production.batch'
    _description = 'Production Order Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_picking_type(self):
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', '=', company_id),
        ], limit=1).id
    
    @api.model
    def _get_default_location_src_id(self):
        location = False
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        if self.env.context.get('default_picking_type_id'):
            location = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id']).default_location_src_id
        if not location:
            location = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
        return location and location.id or False

    @api.model
    def _get_default_location_dest_id(self):
        location = False
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        if self._context.get('default_picking_type_id'):
            location = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id']).default_location_dest_id
        if not location:
            location = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
        return location and location.id or False
    
    @api.model
    def _get_default_date_planned_start(self):
        if self.env.context.get('default_date_deadline'):
            return fields.Datetime.to_datetime(self.env.context.get('default_date_deadline'))
        return datetime.datetime.now()
    
    @api.model
    def _get_default_is_locked(self):
        return self.user_has_groups('mrp.group_locked_by_default')

    name = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'))

    origin = fields.Char(
        'Source', copy=False,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Reference of the document that generated this production order request.")
    
    notes = fields.Text('Note')

    product_id = fields.Many2one('product.product', 'To Consume',
        domain="""[('type', 'in', ['product', 'consu']),'|',('company_id', '=', False),('company_id', '=', company_id)]""",
        readonly=True, required=True, check_company=True,states={'draft': [('readonly', False)]})
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    product_tracking = fields.Selection(related='product_id.tracking')
    product_qty = fields.Float('Quantity To Consume',default=1.0, digits='Product Unit of Measure',readonly=True, required=True, tracking=True,states={'draft': [('readonly', False)]})
    waste_qty = fields.Float('Waste',default=1.0, digits='Product Unit of Measure', readonly=True, store=True, compute='_calculate_waste')
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure',readonly=True, required=True,states={'draft': [('readonly', False)]}, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
    date_planned_start = fields.Datetime('Scheduled Date', copy=False, default=_get_default_date_planned_start,help="Date at which you plan to start the production.",index=True, required=True)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        default=_get_default_picking_type, required=True, check_company=True,
        readonly=True, states={'draft': [('readonly', False)]})
    
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        readonly=True, states={'draft': [('readonly', False)]},
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
    
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,index=True, required=True)
    is_locked = fields.Boolean('Is Locked', default=_get_default_is_locked, copy=False)
    
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group',copy=False)
    propagate_cancel = fields.Boolean('Propagate cancel and split',
        help='If checked, when the previous move of the move (which was generated by a next procurement) is cancelled or split, the move generated by this move will too')

    batch_line_ids = fields.One2many('mrp.production.batch.line', 'batch_id', 'Production Order Batch Line',copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    production_ids = fields.One2many('mrp.production', 'batch_id', 'Production Order Batch',copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    location_src_id = fields.Many2one('stock.location', 'Components Location',
        default=_get_default_location_src_id,
        readonly=True, required=True,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will look for components.")
    
    location_dest_id = fields.Many2one('stock.location', 'Finished Products Location',
        default=_get_default_location_dest_id,
        readonly=True, required=True,
        domain="[('usage','=','internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        states={'draft': [('readonly', False)]}, check_company=True,
        help="Location where the system will stock the finished products.")

    @api.depends(
        'production_ids.state', 'production_ids.product_qty','product_qty')
    def _compute_state(self):
        """ Compute the production state. It use the same process than stock
        picking. It exists 3 extra steps for production:
        - progress: At least one item is produced or consumed.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        # TODO: duplicated code with stock_picking.py
        for production in self:
            if not production.production_ids:
                production.state = 'draft'
            elif all(mo.state == 'draft' for mo in production.production_ids):
                production.state = 'draft'
            elif all(mo.state == 'cancel' for mo in production.production_ids):
                production.state = 'cancel'
            elif all(mo.state in ('cancel', 'done') for mo in production.production_ids):
                production.state = 'done'
            elif any(mo.state in ('confirmed','to_close','cancel', 'done') for mo in production.production_ids):
                production.state = 'progress'
            else:
                production.state = 'confirmed'
    
    @api.onchange('product_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if not self.product_id:
            self.bom_id = False
        elif not self.bom_id or self.bom_id.product_tmpl_id != self.product_tmpl_id or (self.bom_id.product_id and self.bom_id.product_id != self.product_id):
            bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id, company_id=self.company_id.id, bom_type='normal')
            if bom:
                self.bom_id = bom.id
                self.product_qty = self.bom_id.product_qty
                self.product_uom_id = self.bom_id.product_uom_id.id
            else:
                self.bom_id = False
                self.product_uom_id = self.product_id.uom_id.id
    
    
    @api.depends('batch_line_ids.product_qty')
    def _calculate_waste(self):
        qty_produce = 0.0
        for rec in self.batch_line_ids:
            qty_produce += rec.product_qty
        
        if qty_produce <= self.product_qty:
            self.waste_qty = self.product_qty - qty_produce
        else:
            raise UserError(_('Qty produce over than qty consume'))
    

    @api.onchange('product_id', 'product_qty', 'product_uom_id')
    def _onchange_move_raw(self):
        if not self.product_id and not self._origin.product_id:
            return
        # Clear move raws if we are changing the product. In case of creation (self._origin is empty),
        # we need to avoid keeping incorrect lines, so clearing is necessary too.
        if self.product_id != self._origin.product_id:
            self.batch_line_ids = [(5,)]

        if self.product_id and self.product_qty > 0:
            material = self.env['mrp.bom.line'].search([('product_id', '=', self.product_id.id)])
            for material_line in material:
                list_order_raw = [(4, order.id) for order in self.batch_line_ids.filtered(lambda m: not m.product_id)]
                bom_material = material_line.bom_id
                orders_raw_values = self._get_orders_raw_values(bom_material)
                order_raw_dict = {move.product_id.id: move for move in self.batch_line_ids.filtered(lambda m: m.product_id)}
                for order_raw_values in orders_raw_values:
                    if order_raw_values['product_id'] in order_raw_dict:
                        # update existing entries
                        list_order_raw += [(1, order_raw_dict[order_raw_values['product_id']].id, order_raw_values)]
                    else:
                        # add new entries
                        list_order_raw += [(0, 0, order_raw_values)]
                self.batch_line_ids = list_order_raw
    
    def _get_orders_raw_values(self,bom_material):
        moves = []
        for production in self:
            product = self.env['product.product'].search([('product_tmpl_id', '=', bom_material.product_tmpl_id.id)], limit=1)
            moves.append(production._get_order_raw_values(
                product.id,
                bom_material.product_qty,
                bom_material.product_uom_id
            ))
        return moves

    def _get_order_raw_values(self, product_id, product_uom_qty, product_uom):
        source_location = self.location_src_id
        data = {
            'product_id': product_id,
            # 'product_qty': product_uom_qty,
            'product_qty': 0,
            'product_uom_id': product_uom,
        }
        return data
    
    def _action_confirm(self):
        self.state = 'confirmed'

    def action_confirm(self):
        if not self.product_id and not self._origin.product_id:
            return
        
        if self.product_id and self.product_qty > 0:
            for batch_line in self.batch_line_ids:
                if batch_line.product_id and batch_line.product_qty > 0:
                    # makesure bom available
                    bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', batch_line.product_id.product_tmpl_id.id)], limit=1)
                    if bom:
                        list_produce_raw = [(4, produce.id) for produce in self.production_ids.filtered(lambda m: not m.product_id)]
                        files_produce = []
                        data_produce = {
                            'product_id': batch_line.product_id.id,
                            'product_qty': batch_line.product_qty,
                            'qty_producing': batch_line.product_qty,
                            'product_uom_id': batch_line.product_uom_id.id,
                            'bom_id': bom.id,
                            'date_planned_start': self.date_planned_start,
                            'company_id': self.company_id.id,
                            'picking_type_id': self.picking_type_id.id,
                            'location_src_id': self.location_src_id.id,
                            'location_dest_id': self.location_dest_id.id,
                            'batch_line_id': batch_line.id
                        }
                        files_produce.append(data_produce)
                        produces_raw_values = files_produce
                        produce_raw_dict = {produce.product_id.id: produce for produce in self.production_ids.filtered(lambda m: (m.product_id.id == batch_line.product_id.id))}
                        for produce_raw_values in produces_raw_values:
                            if produce_raw_values['product_id'] in produce_raw_dict:
                                # update existing entries
                                list_produce_raw += [(1, produce_raw_dict[produce_raw_values['product_id']].id, produce_raw_values)]
                            else:
                                # add new entries
                                list_produce_raw += [(0, 0, produce_raw_values)]
                        self.production_ids = list_produce_raw
                        self.production_ids.move_finished_ids.write({'date': self.date_planned_start})
            
                        for stock in self.production_ids:
                            list_move_raw = [(4, move.id) for move in stock.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
                            moves_raw_values = stock._get_moves_raw_values()
                            move_raw_dict = {move.bom_line_id.id: move for move in stock.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                            for move_raw_values in moves_raw_values:
                                if move_raw_values['bom_line_id'] in move_raw_dict:
                                    # update existing entries
                                    list_move_raw += [(1, move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                                else:
                                    # add new entries
                                    list_move_raw += [(0, 0, move_raw_values)]
                            
                            for add_material in batch_line.batch_line_material_ids:
                                if add_material.product_id and batch_line.id == stock.batch_line_id.id:
                                    source_location = self.location_src_id
                                    list_adds_material = [(4, material.id) for material in stock.move_raw_ids.filtered(lambda m: not m.add_material_id)]
                                    files_material = []
                                    data_material = {
                                        # 'sequence': bom_line.sequence if bom_line else 10,
                                        'name': self.name,
                                        'date': self.date_planned_start,
                                        'date_deadline': self.date_planned_start,
                                        'add_material_id': add_material.id if add_material else False,
                                        'picking_type_id': self.picking_type_id.id,
                                        'product_id': add_material.product_id.id,
                                        'product_uom_qty': add_material.product_qty,
                                        'product_uom': add_material.product_uom_id.id,
                                        'location_id': self.location_src_id.id,
                                        'location_dest_id': self.product_id.with_company(self.company_id).property_stock_production.id,
                                        'raw_material_production_id': stock.id,
                                        'company_id': self.company_id.id,
                                        'operation_id': None,
                                        'price_unit': add_material.product_id.standard_price,
                                        'procure_method': 'make_to_stock',
                                        'origin': self.name,
                                        'state': 'draft',
                                        'warehouse_id': source_location.get_warehouse().id,
                                        'group_id': self.procurement_group_id.id,
                                        'propagate_cancel': self.propagate_cancel,
                                    }
                                    files_material.append(data_material)
                                    adds_material_values = files_material
                                    add_material_dict = {material.add_material_id.id: material for material in stock.move_raw_ids.filtered(lambda m: m.add_material_id)}
                                    for add_material_values in adds_material_values:
                                        if add_material_values['add_material_id'] in add_material_dict:
                                            # update existing entries
                                            list_move_raw += [(1, add_material_dict[add_material_values['add_material_id']].id, add_material_values)]
                                        else:
                                            # add new entries
                                            list_move_raw += [(0, 0, add_material_values)]

                            stock.move_raw_ids = list_move_raw

                            if stock.product_id and stock.product_qty > 0:
                                stock._create_update_move_finished()
        self.state = 'confirmed'
    @api.model
    def create(self, values):
        if values.get('name', _('New')) == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('mrp.production.batch') or _('New')
        res = super(MrpProductionBatch, self).create(values)
        return res
    
class MrpProductionBatchLine(models.Model):
    """ Production Orders Batch Line """
    _name = 'mrp.production.batch.line'
    _description = 'Production Order Batch Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    batch_id = fields.Many2one('mrp.production.batch', 'Production Order Batch', check_company=True, index=True)
    product_id = fields.Many2one('product.product', 'Produce',
        domain="""[('type', 'in', ['product', 'consu']),'|',('company_id', '=', False),('company_id', '=', company_id)]""",
        readonly=True, required=True, check_company=True,states={'draft': [('readonly', False)]})
    product_qty = fields.Float('Qty To Produce',default=1.0, digits='Product Unit of Measure',readonly=True, required=True, tracking=True,states={'draft': [('readonly', False)]})
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure',readonly=True, required=True,states={'draft': [('readonly', False)]}, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,index=True, required=True)

    batch_line_material_ids = fields.One2many('mrp.production.batch.line.material', 'batch_line_id', 'Production Order Batch Material',copy=False, states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
    
    @api.depends(
        'batch_id.state', 'batch_id.product_qty','product_qty')
    def _compute_state(self):
        """ Compute the production state. It use the same process than stock
        picking. It exists 3 extra steps for production:
        - progress: At least one item is produced or consumed.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        # TODO: duplicated code with stock_picking.py
        for production in self:
            if not production.batch_id.state:
                production.state = 'draft'
            elif all(move.state == 'draft' for move in production.batch_id):
                production.state = 'draft'
            elif all(move.state == 'cancel' for move in production.batch_id):
                production.state = 'cancel'
            elif all(move.state == 'progress' for move in production.batch_id):
                production.state = 'progress'
            elif all(move.state == 'done' for move in production.batch_id):
                production.state = 'done'
            else:
                production.state = 'confirmed'
    
    @api.onchange('product_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

class MrpProductionBatchMaterial(models.Model):
    """ Production Orders Batch Line Material """
    _name = 'mrp.production.batch.line.material'
    _description = 'Production Order Batch Line Material'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    batch_line_id = fields.Many2one('mrp.production.batch.line', 'Production Order Batch Material', check_company=True, index=True)
    product_id = fields.Many2one('product.product', 'Material',
        domain="""[('type', 'in', ['product', 'consu']),'|',('company_id', '=', False),('company_id', '=', company_id)]""",
        required=True, check_company=True)
    product_qty = fields.Float('Qty To Consume',default=1.0, digits='Product Unit of Measure',required=True, tracking=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure',required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,index=True, required=True)

    @api.onchange('product_id', 'company_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    batch_id = fields.Many2one('mrp.production.batch', 'Production Order Batch', check_company=True, index=True)
    batch_line_id = fields.Many2one('mrp.production.batch.line', 'Production Order Batch Line', check_company=True, index=True)

class StockMove(models.Model):
    """ Stock Move """
    _inherit = 'stock.move'

    add_material_id = fields.Many2one('mrp.production.batch.line.material', 'Production Order Batch Line Material', check_company=True, index=True)