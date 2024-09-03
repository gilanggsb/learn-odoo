from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class ThinqApiQuery(models.Model):
    _name = 'thinq.api.query'
    _description = 'Query for API'

    @api.model
    def get_product_stock_by_partner(self,params):
            data = {}
            location = []
            data_product = []
            location_name = ''
            last_location = ''
            where = ' where 1 = 1'
            location_id = params.get('location_id')
            pallete_id = params.get('pallete_id')
            sku = params.get('sku')
            location_id_name = params.get('location_id_name')
            pallete_id_name = params.get('pallete_id_name')
            sku_barcode = params.get('sku_barcode')
            try:
                if location_id:
                    where = " and sq.location_id = "+str(location_id)

                if pallete_id:
                    where += " and sq.package_id = "+str(pallete_id)

                if sku:
                    where += " and pt.sku_number = '"+str(sku)+"'"

                if location_id_name:
                    where = " and sl.name = '"+str(location_id_name)+"'"

                if pallete_id_name:
                    where += " and sqp.name = '"+str(pallete_id_name)+"'"

                if sku_barcode:
                    where += " and pp.barcode = '"+str(sku_barcode)+"'" 

                query = """
                    select 
                        sq.location_id as location_id, sl.name as location_name ,
                        sq.product_id, pt.name as product_name, pt.default_code, 
                        sum(sq.quantity) as qty , 
                        sq.package_id as pallete_id, sqp.name as pallete_name
                    from 
                        stock_quant sq
                        left join stock_quant_package sqp
                        on sq.package_id = sqp.id
                        inner join product_product pp
                        on sq.product_id = pp.id
                        inner join product_template pt
                        on pp.product_tmpl_id = pt.id
                        inner join stock_location sl
                        on sq.location_id = sl.id and sl."usage" = 'internal'
                        %s
                    group 
                        by sq.location_id, sl.name, sq.package_id , sqp.name , sq.product_id , pt.name, pt.default_code
                    order 
                        by sq.location_id
                """
                self.env.cr.execute(query % (where))
                q_result = self.env.cr.dictfetchall()
                count_data = len(q_result)

                location_name = ""
                location_names = []
                for q in q_result:
                    if location_name != q.get('location_name'): 
                        location_name = q.get('location_name')
                        location_names.append(location_name)
                    vals_data = {
                        'location_name': q.get('location_name'),
                        'product_id': q.get('product_id'),
                        'product_name': "["+q.get('default_code')+"] "+q.get('product_name'),
                        'qty': q.get('qty'),
                        'pallete_id': q.get('pallete_id') if q.get('pallete_id') else "",
                        'pallete_name': q.get('pallete_name') if q.get('pallete_name') else "",
                    }
                    data_product.append(vals_data)
                if q_result:
                    data = {
                        'location_name': location_names,
                        'data': data_product
                    }
                    print(data)
                    return data
                else:
                    return False
            except Exception as e:
                ValidationError(e)

    def get_product_stock_by_partner_product_grouped(self,params):
            data = {}
            location = []
            data_product = []
            location_name = ''
            last_location = ''
            where = ' where 1 = 1'
            location_id = params.get('location_id')
            pallete_id = params.get('pallete_id')
            sku = params.get('sku')
            location_id_name = params.get('location_id_name')
            pallete_id_name = params.get('pallete_id_name')
            sku_barcode = params.get('sku_barcode')
            try:
                if location_id:
                    where = " and sq.location_id = "+str(location_id)

                if pallete_id:
                    where += " and sq.package_id = "+str(pallete_id)

                if sku:
                    where += " and pt.sku_number = '"+str(sku)+"'"

                if location_id_name:
                    where = " and sl.name = '"+str(location_id_name)+"'"

                if pallete_id_name:
                    where += " and sqp.name = '"+str(pallete_id_name)+"'"

                if sku_barcode:
                    where += " and pp.barcode = '"+str(sku_barcode)+"'" 

                query = """
with cte_stock as (
select 
    sq.location_id as location_id, sl.name as location_name ,
    sq.product_id, pt.name as product_name, pt.default_code, 
    sum(sq.quantity) as qty , 
    sq.package_id as pallete_id, sqp.name as pallete_name
from 
    stock_quant sq
    left join stock_quant_package sqp
    on sq.package_id = sqp.id
    inner join product_product pp
    on sq.product_id = pp.id
    inner join product_template pt
    on pp.product_tmpl_id = pt.id
    inner join stock_location sl
    on sq.location_id = sl.id and sl."usage" = 'internal'
    %s
group 
    by sq.location_id, sl.name, sq.package_id , sqp.name , sq.product_id , pt.name, pt.default_code
)
select * from (
select 
    null location_id, null location_name, max(product_id) product_id, max(product_name) product_name, max(default_code) default_code, sum(qty) qty, null pallete_id, null pallete_name, 1 sort_helper
from 
    cte_stock
group by
    product_id
union all
select 
    location_id, location_name, product_id, product_name, default_code, qty, pallete_id, pallete_name, 0 sort_helper 
from 
    cte_stock
) src 
order by product_id, sort_helper desc
                """
                self.env.cr.execute(query % (where))
                q_result = self.env.cr.dictfetchall()
                count_data = len(q_result)

                location_name = ""
                location_names = []
                product_names = []
                for q in q_result:
                    if location_name != q.get('location_name') and q.get('sort_helper') != 1: 
                        location_name = q.get('location_name')
                        location_names.append(location_name)
                    if q.get('sort_helper') == 1: 
                        product_names.append(q.get('product_name'))
                    vals_data = {
                        'location_name': q.get('location_name'),
                        'product_id': q.get('product_id'),
                        'product_name': "["+q.get('default_code')+"] "+q.get('product_name'),
                        'qty': q.get('qty'),
                        'pallete_id': q.get('pallete_id') if q.get('pallete_id') else "",
                        'pallete_name': q.get('pallete_name') if q.get('pallete_name') else "",
                        'header' : q.get('sort_helper') if q.get('sort_helper') else 0,
                    }
                    data_product.append(vals_data)
                if q_result:
                    data = {
                        'location_name': location_names,
                        'product_name': product_names,
                        'data': data_product
                    }
                    print(data)
                    return data
                else:
                    return False
            except Exception as e:
                ValidationError(e)

    @api.model
    def get_product_by_customer_id(self,params):
        result = []
        result_line = []
        result_move_line = []
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        total_data = 0
        dom = []
        if params.get('partner_id'):
            partner_id = int(params.get('partner_id'))
            partner = self.env['res.partner'].browse(partner_id)
            if partner:
                if partner.parent_id:
                    parent_id = partner.parent_id.id
                    dom += [('customer_id', '=', parent_id)]
                else:
                    dom += [('customer_id', '=', partner_id)]

        if params.get('search_key'):
            dom += ['|', ('default_code', 'ilike', params.get('search_key')), ('name', 'ilike', params.get('search_key'))]
        
        products = self.env['product.product'].search(dom,order="id desc",offset=offset,limit=limit)
        total_data = self.env['product.product'].search_count(dom)

        if products:
            for p in products:
                result.append({
                    "id": p.id,
                    "code": p.default_code,
                    "name": p.name,
                    "uom_code": p.uom_id.name,
                    "uom_id": p.uom_id.id,
                })
        return result

    @api.model
    def get_access_right_by_partner_id(self,params):
        data = {}
        data_menu = []
        where = ' where 1 = 1'
        partner_id = params.get('partner_id')
        try:
            if partner_id:
                where += " and partner_id = "+str(partner_id)

            query = """
                select partner_id, name from (
                    select partner_id, name, can_view from (
                        select 
                            tuar.partner_id, 
                            tm.name, 
                            tar.can_view, 
                            tar.can_edit, 
                            tar.can_delete, 
                            tar.can_approve 
                        from thinq_access_right_user_rel aru
                            inner join thinq_user_access_right tuar on tuar.id = aru.access_id
                            inner join thinq_access_right tar on aru.user_id = tar.id 
                            inner join thinq_menu tm on tar.menu_id = tm.id
                        ) access_right 
                    where 
                        can_view = true 
                    group by 
                        partner_id, name, can_view
                ) user_access_right
            """
            query += where
            self.env.cr.execute(query)
            q_result = self.env.cr.dictfetchall()
            count_data = len(q_result)
            
            for q in q_result:
                vals_data = {
                    'menu': q.get('name'),
                }
                data_menu.append(vals_data)
            if q_result:
                data = {
                    'data': data_menu
                }
                return data
            else:
                return False
        except Exception as e:
            ValidationError(e)

    @api.model
    def get_general_function_api(self,params):
        result = []
        
        function_name = params.get('function_name')

        try:
            func = getattr(self, function_name)
            result = func(params)
        except AttributeError:
            _logger.warning(self.type + ": Function Name not found")
        
        return result

    def get_customer_by_name(self, params):
        dom = []
        result = []
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        
        if params.get('search_key'):
            dom += [('name', 'ilike', params.get('search_key'))]
        
        obj = self.env['res.partner']
        results = obj.search(dom,order="id desc",offset=offset,limit=limit)
        result_total_data = obj.search_count(dom)

        if results:
            for p in results:
                result.append({
                    "id": p.id,
                    "name": p.name
                })

        return result

    def get_pallete_by_name(self, params):
        dom = []
        result = []
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')
        
        if params.get('search_key'):
            dom += [('name', 'ilike', params.get('search_key'))]
        
        obj = self.env['stock.quant.package']
        results = obj.search(dom,order="id desc",offset=offset,limit=limit)
        result_total_data = obj.search_count(dom)

        if results:
            for p in results:
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "warehouse_owner_id": p.warehouse_owner_id.id
                })

        return result

    def get_location_by_name(self, params):
        dom = []
        result = []
        limit = params['limit'] if params.get('limit') else 100
        offset=params.get('offset')

        if params.get('warehouse_id'):
            val_id = int(params.get('warehouse_id'))
            dom += [('warehouse_id','=',val_id)]
        
        if params.get('usage'):
            val_id = params.get('usage')
            dom += [('usage','=',val_id)]
        
        if params.get('search_key'):
            dom += [('name', 'ilike', params.get('search_key'))]
        
        obj = self.env['stock.location']
        results = obj.search(dom,order="id desc",offset=offset,limit=limit)
        result_total_data = obj.search_count(dom)

        if results:
            for p in results:
                result.append({
                    "id": p.id,
                    "name": p.name
                })

        return result
