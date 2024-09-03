from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class InventoryDashboard(models.Model):
    _name = 'thinq.view.dashboard.inventory'
    _description = 'Inventory Dashboard View'
    _auto = False

    name = fields.Char()
    product_id = fields.Many2one('product.product')
    customer_id = fields.Many2one('res.partner')
    location_id = fields.Many2one('stock.location')
    lot_id = fields.Many2one('stock.production.lot')
    package_id = fields.Many2one('stock.quant.package')
    quantity = fields.Float('Qty')
    warehouse_id = fields.Many2one('stock.warehouse')
    created_date = fields.Datetime('Create Date')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, "thinq_view_dashboard_inventory")
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW thinq_view_dashboard_inventory AS (
            	select 
					row_number() OVER() AS id,
					'' as name,
					sq.product_id,
					pppt.customer_id,
					sq.location_id,
					sq.lot_id,
					sq.package_id,
					sq.quantity,
					loc.warehouse_id,
                    sq.create_date as created_date
				from 
					stock_quant sq 
					inner join 
					(
						select 
							sl.id location_id,
							sw.id warehouse_id 
						from (
							select 
								id, 
								parent_path, 
								NULLIF(split_part(parent_path,'/',3),'')::int as parent_id 
							from 
								stock_location
						) sl left join stock_warehouse sw on sl.parent_id = sw.lot_stock_id 
						where
							sw.id is not null
					) loc on sq.location_id = loc.location_id
					left join 
					(
						select
							pp.id,
							pt.customer_id 
						from 
							product_product pp left join product_template pt
							on pp.product_tmpl_id = pt.id
						where customer_id is not null
					) pppt on sq.product_id = pppt.id
            )'''
        )

class InventoryDashboardCustomer(models.Model):
    _name = 'thinq.view.dashboard.inventory.cust'
    _description = 'Inventory Dashboard View Customer'
    _auto = False

    name = fields.Char()
    customer_id = fields.Many2one('res.partner')
    warehouse_id = fields.Many2one('stock.warehouse')
    total_item = fields.Integer('Total Item Stored')
    total_qty = fields.Float('Total Qty Stored')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, "thinq_view_dashboard_inventory_cust")
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW thinq_view_dashboard_inventory_cust AS (
            	select 
            		row_number() OVER() AS id,
            		'' as name,
            		customer_id, 
            		warehouse_id, 
            		count(product_id) total_item, 
            		sum(quantity) total_qty 
            	from 
            		thinq_view_dashboard_inventory 
            	group by 
            		customer_id, warehouse_id
            )'''
        )

class InventoryDashboardCustomerProduct(models.Model):
    _name = 'thinq.view.dashboard.inventory.cust.product'
    _description = 'Inventory Dashboard View Customer Product'
    _auto = False

    name = fields.Char()
    customer_id = fields.Many2one('res.partner')
    warehouse_id = fields.Many2one('stock.warehouse')
    product_id = fields.Many2one('product.product')
    total_qty = fields.Float('Total Qty Stored')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, "thinq_view_dashboard_inventory_cust_product")
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW thinq_view_dashboard_inventory_cust_product AS (
                select 
                    row_number() OVER() AS id,
                    '' as name,
                    customer_id, 
                    warehouse_id, 
                    product_id, 
                    sum(quantity) total_qty 
                from 
                    thinq_view_dashboard_inventory 
                group by 
                    customer_id, warehouse_id, product_id
            )'''
        )
