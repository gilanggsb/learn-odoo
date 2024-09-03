from odoo import fields,models,api,_


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    production_date = fields.Datetime('Production Date')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    production_date = fields.Datetime('Production Date')

    def _get_value_production_lot(self):
        self.ensure_one()
        return{
            'company_id': self.company_id.id,
            'name': self.lot_name,
            'product_id': self.product_id.id,
            'production_date': self.production_date
        }


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    production_date = fields.Datetime('Production Date', related='lot_id.production_date')