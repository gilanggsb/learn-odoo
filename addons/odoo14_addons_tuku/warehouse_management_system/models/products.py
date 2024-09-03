# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime
from datetime import timedelta, date

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True)
    product_categ = fields.Selection([('always_on','Always ON'),('seasonal', 'Seasonal'),('inactive', 'Inactive')], string='Tuku Category')
    uom_categ = fields.Many2one('uom.category', string='Unit Categories')
    uom_po_factor = fields.Float('Ratio', default=1.0, digits=0, required=True)
    type_uom_po = fields.Selection([('equal','Equal with the reference Unit of Measure'),('bigger','Bigger than the reference Unit of Measure'),('smaller', 'Smaller than the reference Unit of Measure')], string='Type UOM PO', required=True)
    uom_base = fields.Many2one('uom.uom', string='UOM ERP', required=True)
    uom_base_factor = fields.Float('Ratio', default=1.0, digits=0, required=True)
    type_uom_base = fields.Selection([('equal','Equal with the reference Unit of Measure'),('bigger','Bigger than the reference Unit of Measure'),('smaller', 'Smaller than the reference Unit of Measure')], string='Type UOM ERP', required=True)

    @api.onchange('uom_categ')
    def _onchange_uom_categ(self):
        if self.uom_categ:
            self.uom_id = ''
            self.uom_po_id = ''
            self.uom_po_factor = 0.0
            self.uom_base = ''
            self.uom_base_factor = 0.0


class StockInboundFleetLine(models.Model):
    _inherit = "thinq.stock.inbound.fleet.line"
    _description = "Product"
    _rec_name = "product_id"
    _order = "id"

    @api.onchange('product_id')
    def _onchange_lot_ids(self): 
        if self.product_id:
            uom = self.env['product.template'].search([('id','=',self.product_id.product_tmpl_id.id)])
            for this in uom:
                self.product_uom_id = this.uom_po_id