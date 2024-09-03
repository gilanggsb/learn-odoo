# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from types import resolve_bases
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqInheritStockPicking(models.Model):
    _inherit = "stock.picking"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', related='picking_type_id.warehouse_id', readonly=True, store=True, index=True)

    @api.onchange('partner_id', 'partner_id.location_ids', 'picking_type_id', 'picking_type_id.code')
    def onchange_location_from_partner_id(self):
        res = {}
        if not self.partner_id:
            return
        
        if self.partner_id and self.partner_id.mapped('location_ids'):
            if self.picking_type_id and self.picking_type_id.code:
                picking_type_code = self.picking_type_id.code
            else:
                picking_type_code = self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).code
            
            if picking_type_code and picking_type_code == 'outgoing':
                location_list = self.partner_id.mapped('location_ids').ids
                res['domain'] = {'location_dest_id': [('id', 'in', location_list)]}
        return res
    
    @api.model
    def create_picking(self, data):
        pick_type = None
        if data.get('warehouse_id') and data.get('company_id'):
            dom = [('warehouse_id', '=', data.get('warehouse_id')), ('company_id', '=', data.get('company_id'))]
            if data.get('picking_type') in ('internal', 'incoming', 'outgoing'):
                dom += [('code', '=', data.get('picking_type'))]
            else:
                raise ValidationError(_("Picking Type Undefined."))
            pick_type = self.env['stock.picking.type'].search(dom, limit=1)
        
        picking_vals = {
            'partner_id': data.get('partner_id') or False,
            'date': data.get('date') or fields.Datetime.now(),
            'picking_type_id': data.get('picking_type_id') or (pick_type and pick_type.id),
            'location_id': data.get('location_id') or False,
            'location_dest_id': data.get('location_dest_id') or False,
            'company_id': data.get('company_id') or False,
            'user_id': data.get('user_id') or self.env.user.id,
            'scheduled_date': data.get('scheduled_date') or fields.Datetime.now(),
            'origin': data.get('origin') or False,
        }
        if data.get('picking_lines'): #[{}, {}]
            move_line_vals = []
            for l in data.get('picking_lines'):
                move_line_vals.append({
                    'name': l.get('description') or False,
                    'product_id': l.get('product_id') or False,
                    'product_uom_qty': l.get('product_uom_qty') or False,
                    'product_uom': l.get('product_uom') or False,
                    'date': l.get('date') or data.get('date') or fields.Datetime.now(),
                    'date_deadline': l.get('date_deadline') or data.get('scheduled_date') or fields.Datetime.now(),
                    'location_id': l.get('location_id') or data.get('location_id') or False,
                    'location_dest_id': l.get('location_dest_id') or data.get('location_dest_id') or False,
                    'partner_id': l.get('partner_id') or data.get('partner_id') or False,
                    'state': 'draft',
                    'price_unit': l.get('price_unit') or False,
                    'company_id': l.get('company_id') or data.get('company_id') or False,
                    'origin': l.get('origin') or data.get('origin') or False,
                    'warehouse_id': l.get('warehouse_id') or data.get('warehouse_id') or False,
                    'description_picking': l.get('description_picking') or False,
                })
            picking_vals.update({'move_lines': move_line_vals})
        return self.create(picking_vals)
        
    @api.model
    def update_picking(self, picking_id, data):
        update_picking = None
        stock_move_obj = self.env['stock.move']
        picking_values = {}
        if data.get('date'):
            picking_values.update({'date': data.get('date')})
        if data.get('partner_id'):
            picking_values.update({'partner_id': data.get('partner_id')})
        if data.get('location_id'):
            picking_values.update({'location_id': data.get('location_id')})
        if data.get('location_dest_id'):
            picking_values.update({'location_dest_id': data.get('location_dest_id')})
        if data.get('company_id'):
            picking_values.update({'company_id': data.get('company_id')})
        if data.get('user_id'):
            picking_values.update({'user_id': data.get('user_id')})
        if data.get('scheduled_date'):
            picking_values.update({'scheduled_date': data.get('scheduled_date')})
        if data.get('origin'):
            picking_values.update({'origin': data.get('origin')})
        if data.get('picking_type_id'):
            picking_values.update({'picking_type_id': data.get('picking_type_id')})

        if picking_values and isinstance(picking_values, dict):
            if picking_id:
                update_picking = self.browse(picking_id).write(picking_values)
            else:
                if data.get('name'):
                    pickings = self.search([('name', '=', data.get('name'))], limit=1)
                    for p in pickings:
                        update_picking = p.write(picking_values)
        
        if data.get('picking_lines') and isinstance(data['picking_lines'], list): 
            for l in data.get('picking_lines'):
                data_move_lines = {}
                if l.get('name'):
                    data_move_lines.update({'name': l.get('name')})
                if l.get('product_uom_qty'):
                    data_move_lines.update({'product_uom_qty': l.get('product_uom_qty')})
                if l.get('price_unit'):
                    data_move_lines.update({'price_unit': l.get('price_unit')})
                if l.get('product_uom'):
                    data_move_lines.update({'product_uom': l.get('product_uom')})
                if l.get('product_id'):
                    data_move_lines.update({'product_id': l.get('product_id')})
                if l.get('quantity_done'):
                    data_move_lines.update({'quantity_done': l.get('quantity_done')})
                if l.get('date'):
                    data_move_lines.update({'date': l.get('date')})
                if l.get('date_deadline'):
                    data_move_lines.update({'date_deadline': l.get('date_deadline')})
                if l.get('warehouse_id'):
                    data_move_lines.update({'warehouse_id': l.get('warehouse_id')})

                if l.get('move_id'):
                    update_picking_lines = stock_move_obj.browse(int(l.get('move_id'))).write(data_move_lines)
                else:
                    picking_id = picking_id if picking_id else l.get('picking_id')
                    if picking_id and l.get('product_id'):
                        pick_line_existing = stock_move_obj.search([
                            ('picking_id', '=', picking_id), ('product_id', '=', l.get('product_id'))], limit=1)
                        if pick_line_existing:
                            update_picking_lines = pick_line_existing.write(data_move_lines)        
        return update_picking

    @api.model
    def action_create_update_picking(self, data):
        result = None
        for rec in data.get('data'):
            check_duplicate_data = self.checking_picking(rec.get('name'))
            if not check_duplicate_data:
                result = self.create_picking(rec)
            else:
                result = self.update_picking(check_duplicate_data[1].id, rec)
        return result

    @api.model
    def checking_picking(self,picking_ref):
        picking_data = self.search([('name','=',picking_ref),('state','!=','cancel')])
        if picking_data:
            return True,picking_data
        else:
            return False

    @api.model
    def get_list_picking(self, params):
        result = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = []
        if params.get('locationId'):
            dom += [('location_id', '=', params.get('locationId')),('picking_type_id.code','not in',['incoming','outgoing'])]
        if params.get('warehouseId'):
            picking_types = self.env['stock.picking.type'].search([('warehouse_id', '=', params.get('warehouseId'))])
            dom += [('picking_type_id', 'in', tuple(picking_types.ids)),('picking_type_id.code','not in',['incoming','outgoing'])]
        
        if (params.get('locationId') or params.get('warehouseId')) and dom:
            pickings = self.search(dom,offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','not in',['incoming','outgoing'])],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','not in',['incoming','outgoing'])])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','not in',['incoming','outgoing'])],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','not in',['incoming','outgoing'])])
        
        if pickings:
            for p in pickings:
                result.append({
                    "id": p.id,
                    "total_data":total_data,
                    "name": p.name,
                    "scheduled_date": p.scheduled_date,
                    "partner_id": p.partner_id.id,
                    "partner_name": p.partner_id.name,
                    "origin": p.origin,
                    "location_id": p.location_id.id,
                    "source_location": p.location_id.name,
                    "location_dest_id": p.location_dest_id.id,
                    "destination_location": p.location_dest_id.name,
                    "picking_type_id": p.picking_type_id.id,
                    "picking_type_code": p.picking_type_id.code,
                    "company_id": p.company_id.id,
                    "user_id": p.user_id.id,
                    "date": p.date,
                    "state": p.state,
                })
        return result

    @api.model
    def get_list_picking_inbound(self, params):
        result = []
        result_line = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = []
        if params.get('locationId'):
            dom += [('location_id', '=', params.get('locationId')),('picking_type_id.code','=','incoming')]
        if params.get('warehouseId'):
            picking_types = self.env['stock.picking.type'].search([('warehouse_id', '=', params.get('warehouseId'))])
            dom += [('picking_type_id', 'in', tuple(picking_types.ids)),('picking_type_id.code','=','incoming')]
        if params.get('partnerId'):
            partner_id = int(params.get('partnerId'))
            partner_id_obj = self.env['res.partner'].browse(partner_id)
            if partner_id_obj:
                if partner_id_obj.warehouse_ids:
                    dom += [('warehouse_id', 'in', partner_id_obj.warehouse_ids.ids),('picking_type_id.code','=','incoming')]

        if (params.get('locationId') or params.get('warehouseId') or params.get('partnerId')) and dom:
            pickings = self.search(dom,offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','incoming')],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','incoming')])
        
        if pickings:
            for p in pickings:
                if p.move_ids_without_package:  
                    for line in p.move_ids_without_package:
                        vals  = {
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name,
                            "product_uom_qty": line.product_uom_qty,
                            "product_uom": line.product_uom.id,
                            "product_uom_name": line.product_uom.name,
                            "quantity_done": line.quantity_done
                        }
                        result_line.append(vals)   
                result.append({
                    "id": p.id,
                    "total_data":total_data,
                    "name": p.name,
                    "scheduled_date": p.scheduled_date,
                    "partner_id": p.partner_id.id,
                    "partner_name": p.partner_id.name,
                    "origin": p.origin,
                    "location_id": p.location_id.id,
                    "source_location": p.location_id.name,
                    "location_dest_id": p.location_dest_id.id,
                    "destination_location": p.location_dest_id.name,
                    "picking_type_id": p.picking_type_id.id,
                    "picking_type_code": p.picking_type_id.code,
                    "company_id": p.company_id.id,
                    "user_id": p.user_id.id,
                    "date": p.date,
                    "state": p.state,
                    "line_ids": result_line
                })
        return result

    @api.model
    def get_list_picking_outbound(self, params):
        result = []
        result_line = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        dom = []
        total_data = 0
        if params.get('locationId'):
            dom += [('location_id', '=', params.get('locationId')),('picking_type_id.code','=','outgoing')]
        if params.get('warehouseId'):
            picking_types = self.env['stock.picking.type'].search([('warehouse_id', '=', params.get('warehouseId'))])
            dom += [('picking_type_id', 'in', tuple(picking_types.ids)),('picking_type_id.code','=','outgoing')]
        if params.get('partnerId'):
            partner_id = int(params.get('partnerId'))
            partner_id_obj = self.env['res.partner'].browse(partner_id)
            if partner_id_obj:
                if partner_id_obj.warehouse_ids:
                    dom += [('warehouse_id', 'in', partner_id_obj.warehouse_ids.ids),('picking_type_id.code','=','outgoing')]
        
        if (params.get('locationId') or params.get('warehouseId') or params.get('partnerId')) and dom:
            pickings = self.search(dom,offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','outgoing')],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','incoming')])
        
        if pickings:
            for p in pickings:
                if p.move_ids_without_package:  
                    for line in p.move_ids_without_package:
                        vals  = {
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name,
                            "product_uom_qty": line.product_uom_qty,
                            "product_uom": line.product_uom.id,
                            "product_uom_name": line.product_uom.name,
                            "quantity_done": line.quantity_done
                        }
                        result_line.append(vals)
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "total_data":total_data,
                    "scheduled_date": p.scheduled_date,
                    "partner_id": p.partner_id.id,
                    "partner_name": p.partner_id.name,
                    "origin": p.origin,
                    "location_id": p.location_id.id,
                    "source_location": p.location_id.name,
                    "location_dest_id": p.location_dest_id.id,
                    "destination_location": p.location_dest_id.name,
                    "picking_type_id": p.picking_type_id.id,
                    "picking_type_code": p.picking_type_id.code,
                    "company_id": p.company_id.id,
                    "user_id": p.user_id.id,
                    "date": p.date,
                    "state": p.state,
                    "line_ids": result_line
                })
        return result
    
    @api.model
    def get_detail_picking(self, params):
        result = []
        search_query = []
        if len(params.get('searchQuery')) > 0:
            for query in params.get('searchQuery'):
                if type(query).__name__ == 'list':
                    querys = tuple(query)
                    search_query.append(querys)
                else:
                    search_query.append(query)

        if params.get('state') and params['state'] not in (None, [], False, ''):
            search_query.append(('state', '=', str(params.get('state'))))
        else:
            search_query.append(('state', '!=', 'cancel'))
        limit = params['limit'] if params.get('limit') else 100
        search_transfer = self.env['stock.picking'].search(search_query,limit=limit,offset=params.get('offset'),order=params.get('orderBy'))
        total_data = self.env['stock.picking'].search_count(search_query)
        if search_transfer:
            for picking in search_transfer:
                res_move_lines = []
                if picking.move_lines:
                    for pick_line in picking.move_lines:
                        res_move_lines_operation = []
                        if pick_line.move_line_nosuggest_ids:
                            for product_move in pick_line.move_line_nosuggest_ids:
                                res_move_lines_operation.append({
                                'pallet_id': int(product_move.result_package_id.id) or False,
                                'pallet_no': product_move.result_package_id.name or False,
                                'product_id': int(product_move.product_id.id) or False,
                                'product_uom_qty': product_move.product_uom_qty, #Qty Demand
                                'location_dest_id': product_move.location_dest_id.id,
                                'location_dest_name': product_move.location_dest_id.name,
                                'product_uom': int(product_move.product_uom_id.id) or False,
                                'quantity_done': product_move.qty_done, #Qty Done
                            })
                        res_move_lines.append({
                            'name': pick_line.name,
                            'product_id': [int(pick_line.product_id.id),pick_line.product_id.name] if pick_line.product_id else [],
                            'product_uom_qty': pick_line.product_uom_qty, #Qty Demand
                            'price_unit': pick_line.price_unit,
                            'product_uom': [int(pick_line.product_uom.id),pick_line.product_uom.name] if pick_line.product_uom else [],
                            'quantity_done': pick_line.quantity_done, #Qty Done
                            'product_qty': pick_line.product_qty, #Real Quantity
                            'productMoves' : res_move_lines_operation if res_move_lines_operation not in (None, [], False) else []
                        })    
                data_transfer = {
                    "total_data":total_data,
                    "id":picking.id,
                    "name": picking.name,
                    "partner_id": [picking.partner_id.id,picking.partner_id.name] if picking.partner_id else [],
                    "picking_type_id": [picking.picking_type_id.id,picking.picking_type_id.sequence_id.name] if picking.picking_type_id else [],
                    "state": picking.state,
                    "backorder_id": [picking.backorder_id.id,picking.backorder_id.name] if picking.backorder_id else [],
                    "date": picking.date,
                    "date_dead_line": picking.date_deadline,
                    "date_done": picking.date_done,
                    "location_dest_id": picking.location_dest_id.id or False,
                    "location_id": picking.location_id.id or False,
                    "origin": picking.origin,
                    "note": picking.note,
                    "owner_id": [picking.owner_id.id,picking.owner_id.name] if picking.owner_id else [],
                    "sale_id": picking.sale_id.id or False,
                    "scheduled_date": picking.scheduled_date,
                    "user_id": picking.user_id.id or False,
                    "move_type": picking.move_type,
                    "group_id": picking.group_id.id or False,
                    "company_id": picking.company_id.id or False,
                    "priority": picking.priority,
                    "picking_type_code": picking.picking_type_id.code,
                    "picking_lines": res_move_lines if res_move_lines not in (None, [], False) else [],
                    "forklift_id":[picking.forklift_id.id,picking.forklift_id.name] if picking.forklift_id else [],
                    "inbound_fleet_id":[picking.inbound_fleet_id.id,picking.inbound_fleet_id.name] if picking.inbound_fleet_id else [],
                }
                result.append(data_transfer)
        return result

    def action_set_default_qty_and_location(self):
        if self.move_line_nosuggest_ids:
            for line in self.move_line_nosuggest_ids:
                if line.move_id:
                    line.qty_done = line.move_id.product_uom_qty
        return True

class ThinqInheritStockQuant(models.Model):
    _inherit = "stock.quant"

    product_default_code = fields.Char('Item Code', related='product_id.default_code')