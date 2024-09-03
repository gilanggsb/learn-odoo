# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import xlrd

class StockInboundFleetWizard(models.TransientModel):
    _name = 'stock.inbound.fleet.wizard'

    data_file = fields.Binary(string='XLS File')
    file_name = fields.Char('Filename')


    def action_import_stock_inbound_fleet(self):
        new_inbound = None
        inbounds = self.env['thinq.stock.inbound.fleet'].browse(self.env.context.get('active_id'))
        
        if inbounds.state != 'draft':
            raise exceptions.Warning(_("Aborting, transfer must be in Draft status!"))

        inbound_line = self.env['thinq.stock.inbound.fleet.line']
        # for move in inbounds.move_ids_without_package:
        #     self.env.cr.execute("""delete from stock_move where id =%s """%(move.id))
        
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
                new_inbound = self.env['thinq.stock.inbound.fleet.line'].create({
                    'inbound_id': inbounds.id,
                    'product_id': product_id.id,
                    'name' : product_id.name,
                    'product_qty' : qty,
                    'product_uom_id' : product_id.uom_id.id
                })
            else:
                raise exceptions.Warning(_("Aborting, "+product_item_code+" Not Found!"))

        if new_inbound:
            attachment_ids = self.env['ir.attachment'].sudo().create({
                'name': self.file_name,
                'type': 'binary',
                'datas': self.data_file,
                'res_model': 'thinq.stock.inbound.fleet',
                'res_id': inbounds.id,
                'res_name': self.file_name,
                'public' : True
            })
            self.env['mail.message'].sudo().create({
                'body': _('<p>Attached Files : </p>'),
                'model': 'thinq.stock.inbound.fleet',
                'message_type': 'comment',
                'no_auto_thread': False,
                'res_id': inbounds.id,
                'attachment_ids': [(6, 0, attachment_ids.ids)],
            })
        return True