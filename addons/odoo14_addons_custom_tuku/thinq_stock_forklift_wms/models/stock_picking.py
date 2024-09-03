# -*- coding: utf-8 -*-
# © 2021 Thinq Technology
import logging
from types import resolve_bases
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class ThinqForkliftInheritStockPicking(models.Model):
    _inherit = "stock.picking"

    forklift_id = fields.Many2one('thinq.stock.forklift', string='Forklift')

    @api.model
    def get_list_picking_by_userId(self, params):
        result = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = ['|',('picking_id.state','=','confirmed'),('picking_id.state','=','assigned')]

        # ready, in_progress or done
        if params.get('state'):
            dom += [('forklift_state','=',params.get('state'))]

        # incoming or outgoing
        if params.get('picking_type'):
            dom += [('picking_id.picking_type_id.code','=',params.get('picking_type'))]

        if params.get('userId'):
            dom += [('forklift_id.partner_id','=',params.get('userId'))]

        if params.get('userId') and dom:
            pickings = self.env['stock.move.line'].search(dom,order="id desc",offset=offset,limit=limit)
            total_data = self.env['stock.move.line'].search_count(dom)
                
        if pickings:
            for line in pickings:
                p = self.browse(line.picking_id.id)
                result.append({
                    "id": p.id,
                    "total_data":total_data,
                    "name": p.name,
                    "scheduled_date": p.scheduled_date,
                    "partner_id": p.partner_id.id,
                    "partner_name": p.partner_id.name,
                    "origin": p.origin,
                    "move_line_id": line.id,
                    "location_id": line.location_id.id,
                    "source_location": line.location_id.name,
                    "location_dest_id": line.location_dest_id.id,
                    "destination_location": line.location_dest_id.name,
                    "picking_type_id": p.picking_type_id.id,
                    "picking_type_code": p.picking_type_id.code,
                    "company_id": p.company_id.id,
                    "user_id": p.user_id.id,
                    "date": p.date,
                    "state": line.forklift_state,
                    "product_id": line.product_id.id,
                    "product_id_name": line.product_id.name,
                    "product_uom_id": line.product_uom_id.id,
                    "product_uom_id_name": line.product_uom_id.name,
                    "package_id": line.package_id.id if line.package_id else '',
                    "package_id_name": line.package_id.name if line.package_id else '',
                    "result_package_id": line.result_package_id.id if line.result_package_id else '',
                    "result_package_id_name": line.result_package_id.name if line.result_package_id else '',
                    "qty_done": line.qty_done,
                    "product_id_barcode": line.product_id.barcode,
                    "url_product_image": "https://cas-wms-odoo.tech-lab.space/web/image?model=product.product&id="+str(line.product_id.id)+"&field=image_128"
                })
        return result

    @api.model
    def get_list_picking_inbound(self, params):
        result = []
        result_line = []
        result_move_line = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = [('state','=','assigned')]
        
        # searchkey
        if params.get('search_key'):
            dom += [('name','ilike',params.get('search_key'))]

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
            pickings = self.search(dom,order="id desc",offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','=','incoming')])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','incoming')],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','incoming')])
        
        if pickings:
            for p in pickings:
                result_line = []
                result_move_line = []
                if p.move_ids_without_package:  
                    val_line = []
                    for line in p.move_ids_without_package:
                        # val_line  = {
                        #     "id": line.id,
                        #     "product_id": line.product_id.id,
                        #     "product_id_name": line.product_id.name,
                        #     "product_uom": line.product_uom.id,
                        #     "product_uom_name": line.product_uom.name,
                        #     "qty_demand": line.product_uom_qty,
                        #     "qty_done": line.quantity_done
                        # }
                        result_line.append({
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name,
                            "product_uom": line.product_uom.id,
                            "product_uom_name": line.product_uom.name,
                            "qty_demand": line.product_uom_qty,
                            "qty_done": line.quantity_done
                        })
                if p.move_line_ids_without_package:  
                    vals = []
                    for move_line in p.move_line_ids_without_package:
                        # vals  = {
                        #     "id": move_line.id,
                        #     "date": move_line.date,
                        #     "product_id": move_line.product_id.id,
                        #     "product_id_name": move_line.product_id.name,
                        #     "location_id": move_line.location_id.id if move_line.location_id else '',
                        #     "location_id_name": move_line.location_id.name if move_line.location_id else '',
                        #     "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                        #     "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                        #     "product_uom_id": move_line.product_uom_id.id,
                        #     "product_uom_id_name": move_line.product_uom_id.name,
                        #     "qty_reserved": move_line.product_uom_qty,
                        #     "qty_done": move_line.qty_done,
                        #     "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                        #     "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                        #     "package_id": move_line.package_id.id if move_line.package_id else '',
                        #     "package_id_name": move_line.package_id.name if move_line.package_id else '',
                        #     "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                        #     "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        # }
                        result_move_line.append({
                            "id": move_line.id,
                            "date": move_line.date,
                            "product_id": move_line.product_id.id,
                            "product_id_name": move_line.product_id.name,
                            "location_id": move_line.location_id.id if move_line.location_id else '',
                            "location_id_name": move_line.location_id.name if move_line.location_id else '',
                            "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                            "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                            "product_uom_id": move_line.product_uom_id.id,
                            "product_uom_id_name": move_line.product_uom_id.name,
                            "qty_reserved": move_line.product_uom_qty,
                            "qty_done": move_line.qty_done,
                            "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                            "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                            "package_id": move_line.package_id.id if move_line.package_id else '',
                            "package_id_name": move_line.package_id.name if move_line.package_id else '',
                            "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                            "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        })   
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
                    "line_ids": result_line,
                    "move_line_ids": result_move_line
                })
        return result

    @api.model
    def get_list_picking_outbound(self, params):
        result = []
        result_line = []
        result_move_line = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        dom = [('state','=','assigned')]
        total_data = 0

        # searchkey
        if params.get('search_key'):
            dom += [('name','ilike',params.get('search_key'))]

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
            pickings = self.search(dom,order="id desc",offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','=','outgoing')],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','=','outgoing')])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','outgoing')],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','outgoing')])
        
        if pickings:
            for p in pickings:
                result_line = []
                result_move_line = []
                if p.move_ids_without_package:  
                    val_line = []
                    for line in p.move_ids_without_package:
                        # val_line  = {
                        #     "id": line.id,
                        #     "product_id": line.product_id.id,
                        #     "product_id_name": line.product_id.name,
                        #     "product_uom_qty": line.product_uom_qty,
                        #     "product_uom": line.product_uom.id,
                        #     "product_uom_name": line.product_uom.name,
                        #     "quantity_done": line.quantity_done
                        # }
                        result_line.append({
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name,
                            "product_uom": line.product_uom.id,
                            "product_uom_name": line.product_uom.name,
                            "qty_done": line.quantity_done,
                            "qty_demand": line.product_uom_qty
                        })
                if p.move_line_ids_without_package:
                    vals = []  
                    for move_line in p.move_line_ids_without_package:
                        # vals  = {
                        #     "id": move_line.id,
                        #     "date": move_line.date,
                        #     "product_id": move_line.product_id.id,
                        #     "product_id_name": move_line.product_id.name,
                        #     "location_id": move_line.location_id.id if move_line.location_id else '',
                        #     "location_id_name": move_line.location_id.name if move_line.location_id else '',
                        #     "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                        #     "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                        #     "product_uom_id": move_line.product_uom_id.id,
                        #     "product_uom_id_name": move_line.product_uom_id.name,
                        #     "qty_reserved": move_line.product_uom_qty,
                        #     "qty_done": move_line.qty_done,
                        #     "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                        #     "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                        #     "package_id": move_line.package_id.id if move_line.package_id else '',
                        #     "package_id_name": move_line.package_id.name if move_line.package_id else '',
                        #     "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                        #     "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        # }
                        result_move_line.append({
                            "id": move_line.id,
                            "date": move_line.date,
                            "product_id": move_line.product_id.id,
                            "product_id_name": move_line.product_id.name,
                            "location_id": move_line.location_id.id if move_line.location_id else '',
                            "location_id_name": move_line.location_id.name if move_line.location_id else '',
                            "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                            "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                            "product_uom_id": move_line.product_uom_id.id,
                            "product_uom_id_name": move_line.product_uom_id.name,
                            "qty_reserved": move_line.product_uom_qty,
                            "qty_done": move_line.qty_done,
                            "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                            "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                            "package_id": move_line.package_id.id if move_line.package_id else '',
                            "package_id_name": move_line.package_id.name if move_line.package_id else '',
                            "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                            "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        })
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
                    "line_ids": result_line,
                    "move_line_ids": result_move_line
                })
        return result

    @api.model
    def get_list_picking_internal(self, params):
        result = []
        result_line = []
        result_move_line = []
        pickings = None
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        dom = [('state','=','assigned')]
        total_data = 0
        
        # searchkey
        if params.get('search_key'):
            dom += [('name','ilike',params.get('search_key'))]

        if params.get('locationId'):
            dom += [('location_id', '=', params.get('locationId')),('picking_type_id.code','=','internal')]
        if params.get('warehouseId'):
            picking_types = self.env['stock.picking.type'].search([('warehouse_id', '=', params.get('warehouseId'))])
            dom += [('picking_type_id', 'in', tuple(picking_types.ids)),('picking_type_id.code','=','internal')]
        if params.get('partnerId'):
            partner_id = int(params.get('partnerId'))
            partner_id_obj = self.env['res.partner'].browse(partner_id)
            if partner_id_obj:
                if partner_id_obj.warehouse_ids:
                    dom += [('warehouse_id', 'in', partner_id_obj.warehouse_ids.ids),('picking_type_id.code','=','internal')]
        
        if (params.get('locationId') or params.get('warehouseId') or params.get('partnerId')) and dom:
            pickings = self.search(dom,order="id desc",offset=offset,limit=limit)
            total_data = self.search_count(dom)
        elif params.get('pickingId'):
            pickings = self.search([('id', '=', params.get('pickingId')),('picking_type_id.code','=','internal')],offset=offset,limit=limit)
            total_data = self.search_count([('id', '=', params.get('pickingId')),('picking_type_id.code','=','internal')])
        elif params.get('pickingNumber'):
            pickings = self.search([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','internal')],offset=offset,limit=limit)
            total_data = self.search_count([('name', '=', params.get('pickingNumber')),('picking_type_id.code','=','internal')])
        
        if pickings:
            for p in pickings:
                result_line = []
                result_move_line = []
                if p.move_ids_without_package:  
                    val_line = []
                    for line in p.move_ids_without_package:
                        # val_line  = {
                        #     "id": line.id,
                        #     "product_id": line.product_id.id,
                        #     "product_id_name": line.product_id.name,
                        #     "product_uom_qty": line.product_uom_qty,
                        #     "product_uom": line.product_uom.id,
                        #     "product_uom_name": line.product_uom.name,
                        #     "quantity_done": line.quantity_done
                        # }
                        result_line.append({
                            "id": line.id,
                            "product_id": line.product_id.id,
                            "product_id_name": line.product_id.name,
                            "product_uom": line.product_uom.id,
                            "product_uom_name": line.product_uom.name,
                            "qty_done": line.quantity_done,
                            "qty_demand": line.product_uom_qty
                        })
                if p.move_line_ids_without_package:
                    vals = []  
                    for move_line in p.move_line_ids_without_package:
                        # vals  = {
                        #     "id": move_line.id,
                        #     "date": move_line.date,
                        #     "product_id": move_line.product_id.id,
                        #     "product_id_name": move_line.product_id.name,
                        #     "location_id": move_line.location_id.id if move_line.location_id else '',
                        #     "location_id_name": move_line.location_id.name if move_line.location_id else '',
                        #     "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                        #     "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                        #     "product_uom_id": move_line.product_uom_id.id,
                        #     "product_uom_id_name": move_line.product_uom_id.name,
                        #     "qty_reserved": move_line.product_uom_qty,
                        #     "qty_done": move_line.qty_done,
                        #     "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                        #     "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                        #     "package_id": move_line.package_id.id if move_line.package_id else '',
                        #     "package_id_name": move_line.package_id.name if move_line.package_id else '',
                        #     "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                        #     "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        # }
                        result_move_line.append({
                            "id": move_line.id,
                            "date": move_line.date,
                            "product_id": move_line.product_id.id,
                            "product_id_name": move_line.product_id.name,
                            "location_id": move_line.location_id.id if move_line.location_id else '',
                            "location_id_name": move_line.location_id.name if move_line.location_id else '',
                            "location_dest_id": move_line.location_dest_id.id if move_line.location_dest_id else '',
                            "location_dest_id_name": move_line.location_dest_id.name if move_line.location_dest_id else '',
                            "product_uom_id": move_line.product_uom_id.id,
                            "product_uom_id_name": move_line.product_uom_id.name,
                            "qty_reserved": move_line.product_uom_qty,
                            "qty_done": move_line.qty_done,
                            "forklift_id": move_line.forklift_id.id if move_line.forklift_id else '',
                            "forklift_id_name": move_line.forklift_id.name if move_line.forklift_id else '',
                            "package_id": move_line.package_id.id if move_line.package_id else '',
                            "package_id_name": move_line.package_id.name if move_line.package_id else '',
                            "result_package_id": move_line.result_package_id.id if move_line.result_package_id else '',
                            "result_package_id_name": move_line.result_package_id.name if move_line.result_package_id else '',
                        })
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
                    "line_ids": result_line,
                    "move_line_ids": result_move_line
                })
        return result

    @api.model
    def create_stock_picking_internal_transfer(self,params):
        warehouse_id = self.env['stock.warehouse'].browse(params.get('warehouse_id'))

        product_ids = self.env['product.product'].search([('barcode','=',params.get('product_id_barcode'))])
        if len(product_ids) > 0:
            product_id = self.env['product.product'].browse(product_ids[0].id)
        location_ids = self.env['stock.location'].search([('name','=',params.get('location_id_barcode'))])
        if len(location_ids) > 0:
            location_id = location_ids[0].id
        location_dest_ids = self.env['stock.location'].search([('name','=',params.get('location_dest_id_barcode'))])
        if len(location_dest_ids) > 0:
            location_dest_id = location_dest_ids[0].id

        qty_done = params.get('qty_done')
        picking_id = False
        new_stock_picking = None
        
        picking_type_id = warehouse_id.int_type_id
        new_stock_picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type_id.id,
                'location_id' : location_id,
                'location_dest_id' : location_dest_id,
        })
        picking_id = new_stock_picking.id
        
        new_stock_move = self.env['stock.move'].create({
            'picking_id': picking_id,
            'product_id': product_id.id,
            'name' : product_id.name,
            'product_uom_qty' : qty_done,
            'product_uom' : product_id.uom_id.id,
            'location_id' : location_id,
            'location_dest_id' : location_dest_id
        })
        result = []
        if picking_id:
            new_stock_picking.action_confirm()
            new_stock_picking.action_assign()
            for line in new_stock_picking.move_line_ids_without_package:
                line.qty_done = qty_done
                line.location_id = location_id
                line.location_dest_id = location_dest_id
            new_stock_picking.button_validate()
            result.append({
                "status" : 'success',
                "move_line_id": picking_id,
            })
        else:
            result.append({
                "status" : 'error'
            })
        return result

class ThinqForkliftInheritStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    forklift_id = fields.Many2one('thinq.stock.forklift', string='Forklift')
    forklift_state = fields.Selection([
        ('ready', 'Ready'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')], string="Forklift Status", default='ready')

    @api.model
    def create_stock_move_line(self, params):
        picking_id = params.get('picking_id')
        product_id = params.get('product_id')
        if params.get('product_id_barcode'):
            product_ids = self.env['product.product'].search([('barcode','=',params.get('product_id_barcode'))])
            if len(product_ids) > 0:
                product_id = product_ids[0].id
        location_id = params.get('location_id')
        if params.get('location_id_barcode'):
            location_ids = self.env['stock.location'].search([('name','=',params.get('location_id_barcode'))])
            if len(location_ids) > 0:
                location_id = location_ids[0].id
        location_dest_id = params.get('location_dest_id')
        if params.get('location_dest_id_barcode'):
            location_dest_ids = self.env['stock.location'].search([('name','=',params.get('location_dest_id_barcode'))])
            if len(location_dest_ids) > 0:
                location_dest_id = location_dest_ids[0].id
        package_id =  params.get('package_id')
        if params.get('package_id_barcode'):
            package_ids = self.env['stock.quant.package'].search([('name','=',params.get('package_id_barcode'))])
            if len(package_ids) > 0:
                package_id = package_ids[0].id
        result_package_id =  params.get('result_package_id')
        if params.get('result_package_id_barcode'):
            result_package_ids = self.env['stock.quant.package'].search([('name','=',params.get('result_package_id_barcode'))])
            if len(result_package_ids) > 0:
                result_package_id = result_package_ids[0].id
        forklift_id =  params.get('forklift_id')
        product_uom_id =  params.get('product_uom_id')
        qty_done =  params.get('qty_done')
        move_line = self.env['stock.move.line'].create({
            "picking_id": picking_id,
            "product_id": product_id,
            "location_id": location_id,
            "location_dest_id": location_dest_id,
            "package_id": package_id,
            "result_package_id": result_package_id,
            "forklift_id": forklift_id,
            "product_uom_id": product_uom_id,
            "qty_done": qty_done
        })
        move_line_id = move_line.id
        result = []
        if move_line_id:
            result.append({
                "status" : 'success',
                "move_line_id": move_line_id,
            })
        else:
            result.append({
                "status" : 'error'
            })
        return result

    @api.model
    def update_stock_move_line(self, params):
        move_line_id = params.get('id')
        location_id = params.get('location_id')
        location_dest_id = params.get('location_dest_id')
        forklift_state = params.get('state')
        if params.get('location_id_barcode'):
            location_ids = self.env['stock.location'].search([('name','=',params.get('location_id_barcode'))])
            if len(location_ids) > 0:
                location_id = location_ids[0].id
        if params.get('location_dest_id_barcode'):
            location_ids = self.env['stock.location'].search([('name','=',params.get('location_dest_id_barcode'))])
            if len(location_ids) > 0:
                location_dest_id = location_ids[0].id
        package_id =  params.get('package_id')
        if params.get('package_id_barcode'):
            package_ids = self.env['stock.quant.package'].search([('name','=',params.get('package_id_barcode'))])
            if len(package_ids) > 0:
                package_id = package_ids[0].id
        result_package_id =  params.get('result_package_id')
        if params.get('result_package_id_barcode'):
            result_package_ids = self.env['stock.quant.package'].search([('name','=',params.get('package_id_barcode'))])
            if len(result_package_ids) > 0:
                result_package_id = result_package_ids[0].id
        forklift_id =  params.get('forklift_id')
        qty_done =  params.get('qty_done')
        move_line_obj = self.env['stock.move.line'].browse(move_line_id)
        if move_line_obj:
            if forklift_state:
                move_line_obj.write({
                    "forklift_state": forklift_state,
                })
            else:
                move_line_obj.write({
                    "location_id": location_id,
                    "location_dest_id": location_dest_id,
                    "package_id": package_id,
                    "result_package_id": result_package_id,
                    "forklift_id": forklift_id,
                    "qty_done": qty_done,
                })
        result = []
        if move_line_id:
            result.append({
                "status" : 'success',
                "move_line_id": move_line_id,
            })
        else:
            result.append({
                "status" : 'error'
            })
        return result
