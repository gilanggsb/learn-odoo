# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_carrier_details(self):
        """ Return the shipper name and tracking number if any. """
        self.ensure_one()
        return self.carrier_id and self.carrier_id.name, self.carrier_tracking_ref

    def _check_carrier_details_compliance(self):
        amazon_pickings_sudo = self.sudo().filtered(
            lambda p: p.sale_id and p.sale_id.amazon_order_ref \
                      and p.location_dest_id.usage == 'customer'
        )  # In sudo mode to read the field on sale.order
        for picking_sudo in amazon_pickings_sudo:
            carrier_sudo, carrier_tracking_ref = picking_sudo._get_carrier_details()
            if not carrier_sudo:
                raise UserError(_(
                    "Starting from July 2021, Amazon requires that a tracking reference is "
                    "provided with each delivery. See https://odoo.com/r/amz_tracking_ref \n"
                    "To get one, select a carrier."
                ))
            if not carrier_tracking_ref:
                raise UserError(_(
                    "Starting from July 2021, Amazon requires that a tracking reference is "
                    "provided with each delivery. See https://odoo.com/r/amz_tracking_ref \n"
                    "Since your chosen carrier doesn't provide a tracking reference, "
                    "please, enter one manualy."
                ))
        return super()._check_carrier_details_compliance()
