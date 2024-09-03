import base64
import io
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date


class MinimumStockXlsx(models.AbstractModel):
    _name = "report.warehouse_management_system.minimum_stock_report_excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, stock):
        sheet = workbook.add_worksheet('Minimum Stock Report')
        bold = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter'})
        header = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        date_style = workbook.add_format({'text_wrap': True, 'align': 'center', 'num_format': 'yyyy-mm-dd HH:MM:SS'})
        number_style = workbook.add_format({'text_wrap': True, 'align': 'right', 'valign': 'vcenter', 'num_format': '##,##0'})

        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 50)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)

        sheet.set_row(0, 28)
        sheet.write(0, 0, data['filename'], bold)

        row = 3
        col = 0
        sheet.set_row(row, 28)

        sheet.write(row, col, 'Code', header)
        sheet.write(row, col+1, 'Product', header)
        sheet.write(row, col+2, 'Location', header)
        sheet.write(row, col+3, 'On Hand', header)
        sheet.write(row, col+4, 'Minimum Quantity', header)
        sheet.write(row, col+5, 'Buffer Quantity', header)
        sheet.write(row, col+6, 'To Order', header)

        row = 4
        rules = self.env['stock.warehouse.orderpoint'].search([('product_min_qty','>',0)])
        for res in rules:
            qty_ref = res.product_min_qty + res.qty_buffer
            qty_order = 0
            if res.qty_on_hand < qty_ref:
                qty_order = qty_ref - res.qty_on_hand
                sheet.write(row, col, res.product_id.product_tmpl_id.default_code)
                sheet.write(row, col+1, res.product_id.name)
                sheet.write(row, col+2, res.location_id.complete_name)
                sheet.write(row, col+3, res.qty_on_hand, number_style)
                sheet.write(row, col+4, res.product_min_qty, number_style)
                sheet.write(row, col+5, res.qty_buffer, number_style)
                sheet.write(row, col+6, qty_order, number_style)
                row += 1