from odoo import _, api, fields, models
from datetime import datetime

class ReportDailyInventory(models.AbstractModel):
    _name = 'report.thinq_stock_wms.report_daily_inventory'

    def get_product_id(self,date_from,date_to):
        query_parent = """
            select sml.product_id, pt.id as tmpl_id, pt.name, sl.id as location_id, sl.name as location_name, sum(qty_done) as qty_move from stock_move_line sml
            inner join product_product pp on sml.product_id = pp.id
            inner join product_template pt on pp.product_tmpl_id = pt.id
            inner join stock_picking sp on sp.id = sml.picking_id 
            inner join stock_location sl on sp.location_id = sl.id 
            where sml."date" between '%s' and '%s'
            group by sml.product_id, pt.name, pt.id , sl.id, sl.name 
            order by sml.product_id, sl.id
        """

        self.env.cr.execute(query_parent % (str(date_from+" 00:00:00"),str(date_to+" 00:00:00")))

        return self.env.cr.dictfetchall()

    def get_stock_quant(self,product_id,location_id):
        query_parent = """
            select product_id , location_id , sum(quantity) as qty_stock from stock_quant sq
            where product_id = %s and location_id = %s
            group by product_id , location_id 
        """

        self.env.cr.execute(query_parent % (product_id,location_id))

        return self.env.cr.dictfetchall()

    def get_detail(self,date_from,date_to):
        query_parent = """
            select sml.product_id, pt.name, sp.name as picking_name, sl.id as location_id, sl.name as location , sl2.name as location_dest , sml.qty_done from stock_move_line sml
            inner join product_product pp on sml.product_id = pp.id
            inner join product_template pt on pp.product_tmpl_id = pt.id
            inner join stock_picking sp on sp.id = sml.picking_id 
            inner join stock_location sl on sp.location_id = sl.id 
            inner join stock_location sl2 on sp.location_dest_id = sl2.id
            where sml."date" between '%s' and '%s'
            order by sml.product_id
        """

        self.env.cr.execute(query_parent % (str(date_from+" 00:00:00"),str(date_to+" 00:00:00")))

        return self.env.cr.dictfetchall()

    def get_stock_avail(self,data,details):
        datas = []
        datas_parent = []
        datas_product = []
        product_id_temp = False
        for product in data:
            # if product_id_temp != product.get('product_id') :
            #     datas_product = []
            #     vals_parent = {
            #         'product_id' : product.get('product_id'),
            #         'product_name' : product.get('name')
            #     }
            # stock_quant = self.env['stock.quant'].search([('product_id','=',product.get('product_id')),('location_id','=',product.get('location_id'))])

            stock_quant = self.get_stock_quant(product.get('product_id'),product.get('location_id'))
            stock_avali = stock_quant[0].get('qty_stock') if stock_quant else 0
            vals = {
                'product_id':product.get('product_id'),
                'name':product.get('name'),
                'location_id':product.get('location_id'),
                'location_name':product.get('location_name'),
                'qty_before_move':stock_avali + product.get('qty_move'),
                'qty_move':product.get('qty_move') or 0,
                'qty_available':stock_avali,
                'detail': list(filter(lambda d: d['product_id'] == product.get('product_id') and d['location_id'] == product.get('location_id'), details))
            }
            datas_product.append(vals)

        print(datas_product)
        return datas_product

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['data'].get('date_from')
        date_to = data['data'].get('date_to')

        product_ids = self.get_product_id(date_from,date_to)
        details = self.get_detail(date_from,date_to)
        product_datas = self.get_stock_avail(product_ids,details)
        # print(product_ids)
        print(product_datas)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_from': data['form']['date_from_str'],
            'date_to': data['form']['date_to_str'],
            'product_datas': product_datas
        }