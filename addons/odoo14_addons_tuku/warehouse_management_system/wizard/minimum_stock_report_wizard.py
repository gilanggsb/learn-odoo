import string
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timedelta

class MinimumStockWizard(models.TransientModel):
    _name = "stock.warehouse.orderpoint.wizard"

    date_report = fields.Date(string='Date Report', default=datetime.now())

    def export_xls(self):
        filename = 'Minimum Stock Report %s.xls' % (fields.Date.to_string(self.date_report))
        data = {
            'date_report': self.date_report,
            'filename':filename
        }
        
        self.env.ref('warehouse_management_system.minimum_stock_report_xlsx').report_file = filename
        return self.env.ref('warehouse_management_system.minimum_stock_report_xlsx').report_action(self, data=data)
