# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import xlrd
# try:
#     import xlrd
# except ImportError:
#     _logger.debug('Cannot `import xlrd`.')

class StockImportWizard(models.TransientModel):
    _name = 'stock.import.wizard'

    data_file = fields.Binary(string='XLS File')
    file_name = fields.Char('Filename')

    def _find_lot_id(self, lot_name, product):
        lot = self.env['stock.production.lot'].sudo().search([('name', '=', lot_name), ('product_id', '=', product.id)], limit=1)
        return lot and lot.id or False

    def action_import(self):
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        move_line = self.env['stock.move.line']
        for move in picking.move_lines:
            self.env.cr.execute("""delete from stock_move_line where move_id =%s """%(move.id))
            if not self.file_name:
                return False
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.data_file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            reader = []
            keys = sheet.row_values(0)
            values = [sheet.row_values(i) for i in range(1, sheet.nrows)]
            for value in values:
                reader.append(dict(zip(keys, value)))

            if len(reader) > move.product_uom_qty:
                raise exceptions.Warning(_("Qty not more than initial demand!"))

            for line in reader:
                lot_name = int(line.get('Lot'))if isinstance(line.get('Lot'), float) else line.get('Lot')
                vals = {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'picking_id': move.picking_id.id,
                    'lot_name': lot_name if move.picking_code == 'incoming' else False,
                    'lot_id' : self._find_lot_id(lot_name, move.product_id) if move.picking_code in ('outgoing', 'internal') else False,
                    'qty_done': 1 if move.product_id.tracking == 'serial' else line.get('Qty'),
                }
                move_line |= self.env['stock.move.line'].create(vals)

        if move_line:
            attachment_ids = self.env['ir.attachment'].sudo().create({
                'name': self.file_name,
                'type': 'binary',
                'datas': self.data_file,
                'res_model': 'stock.picking',
                'res_id': move.picking_id and move.picking_id.id,
                'res_name': self.file_name,
                'public' : True
            })
            self.env['mail.message'].sudo().create({
                'body': _('<p>Attached Files : </p>'),
                'model': 'stock.picking',
                'message_type': 'comment',
                'no_auto_thread': False,
                'res_id': move.picking_id.id,
                'attachment_ids': [(6, 0, attachment_ids.ids)],
            })
        return True

    def action_import_stock_move(self):
        new_stock_move = None
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        
        if picking.state != 'draft':
            raise exceptions.Warning(_("Aborting, transfer must be in Draft status!"))

        move_line = self.env['stock.move']
        for move in picking.move_ids_without_package:
            self.env.cr.execute("""delete from stock_move where id =%s """%(move.id))
        
        if not self.file_name:
            return False
        try:
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.data_file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise exceptions.Warning(_("Invalid file!"))

        reader = []
        keys = sheet.row_values(0)
        values = [sheet.row_values(i) for i in range(1, sheet.nrows)]
        for value in values:
            reader.append(dict(zip(keys, value)))

        for line in reader:
            product_item_code = int(line.get('Item Code'))if isinstance(line.get('Item Code'), float) else line.get('Item Code')
            product_ids = self.env['product.product'].search([('default_code', '=', product_item_code)])
            if len(product_ids) > 0:
                qty = line.get('Qty')
                product_id = product_ids[0]
                new_stock_move = self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': product_id.id,
                    'name' : product_id.name,
                    'product_uom_qty' : qty,
                    'product_uom' : product_id.uom_id.id,
                    'location_id' : picking.location_id.id,
                    'location_dest_id' : picking.location_dest_id.id
                })
            else:
                raise exceptions.Warning(_("Aborting, "+product_item_code+" Not Found!"))

        if new_stock_move:
            attachment_ids = self.env['ir.attachment'].sudo().create({
                'name': self.file_name,
                'type': 'binary',
                'datas': self.data_file,
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'res_name': self.file_name,
                'public' : True
            })
            self.env['mail.message'].sudo().create({
                'body': _('<p>Attached Files : </p>'),
                'model': 'stock.picking',
                'message_type': 'comment',
                'no_auto_thread': False,
                'res_id': picking.id,
                'attachment_ids': [(6, 0, attachment_ids.ids)],
            })
        return True