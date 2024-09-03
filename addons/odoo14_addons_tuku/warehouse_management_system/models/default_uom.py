# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError

class UoM(models.Model):
    _inherit = 'uom.uom'
    _description = 'Product Unit of Measure'
    _order = "name"


    def _compute_quantity(self, qty, to_unit, product, round=True, rounding_method='UP', raise_if_failure=True):
        """ Convert the given quantity from the current UoM `self` into a given one
            :param qty: the quantity to convert
            :param to_unit: the destination UoM record (uom.uom)
            :param raise_if_failure: only if the conversion is not possible
                - if true, raise an exception if the conversion is not possible (different UoM category),
                - otherwise, return the initial quantity
        """
        if not self or not qty:
            return qty
        self.ensure_one()

        if self == to_unit:
            amount = qty
        else:
            if self not in (product.uom_po_id,product.uom_base):
                raise UserError(_('The unit of measure %s doesn\'t defined on the product [%s] - %s.') % (self.name, product.default_code, product.name))
            else:
                if self == product.uom_po_id:
                    if product.type_uom_po == 'smaller':
                        amount = qty / product.uom_po_factor
                    elif product.type_uom_po == 'bigger':
                        amount = qty * product.uom_po_factor
                    else:
                        amount = qty

                if self == product.uom_base:
                    if product.type_uom_base == 'smaller':
                        amount = qty / product.uom_base_factor
                    elif product.type_uom_base == 'bigger':
                        amount = qty * product.uom_base_factor
                    else:
                        amount = qty

        if to_unit and round:
            amount = tools.float_round(amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)

        return amount
    
    def _adjust_uom_quantities(self, qty, quant_uom, product):
        """ This method adjust the quantities of a procurement if its UoM isn't the same
        as the one of the quant and the parameter 'propagate_uom' is not set.
        """
        procurement_uom = self
        computed_qty = qty
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if get_param('stock.propagate_uom') != '1':
            computed_qty = self._compute_quantity(qty, quant_uom, product, rounding_method='HALF-UP')
            procurement_uom = quant_uom
        else:
            computed_qty = self._compute_quantity(qty, procurement_uom, product, rounding_method='HALF-UP')
        return (computed_qty, procurement_uom)