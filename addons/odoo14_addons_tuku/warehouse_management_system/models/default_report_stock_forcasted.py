# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, models
from odoo.tools import float_is_zero, format_datetime, format_date, float_round


class ReplenishmentReport(models.AbstractModel):
    _inherit = 'report.stock.report_product_product_replenishment'
    _description = "Stock Replenishment Report"    

    def _get_report_lines(self, product_template_ids, product_variant_ids, wh_location_ids):
        def _rollup_move_dests(move, seen):
            for dst in move.move_dest_ids:
                if dst.id not in seen:
                    seen.add(dst.id)
                    _rollup_move_dests(dst, seen)
            return seen

        def _reconcile_out_with_ins(lines, out, ins, demand, only_matching_move_dest=True):
            index_to_remove = []
            for index, in_ in enumerate(ins):
                if float_is_zero(in_['qty'], precision_rounding=out.product_id.uom_id.rounding):
                    continue
                if only_matching_move_dest and in_['move_dests'] and out.id not in in_['move_dests']:
                    continue
                taken_from_in = min(demand, in_['qty'])
                demand -= taken_from_in
                lines.append(self._prepare_report_line(taken_from_in, move_in=in_['move'], move_out=out))
                in_['qty'] -= taken_from_in
                if in_['qty'] <= 0:
                    index_to_remove.append(index)
                if float_is_zero(demand, precision_rounding=out.product_id.uom_id.rounding):
                    break
            for index in index_to_remove[::-1]:
                ins.pop(index)
            return demand

        in_domain, out_domain = self._move_confirmed_domain(
            product_template_ids, product_variant_ids, wh_location_ids
        )
        outs = self.env['stock.move'].search(out_domain, order='priority desc, date, id')
        outs_per_product = defaultdict(lambda: [])
        for out in outs:
            outs_per_product[out.product_id.id].append(out)
        ins = self.env['stock.move'].search(in_domain, order='priority desc, date, id')
        ins_per_product = defaultdict(lambda: [])
        for in_ in ins:
            ins_per_product[in_.product_id.id].append({
                'qty': in_.product_qty,
                'move': in_,
                'move_dests': _rollup_move_dests(in_, set())
            })
        currents = {c['id']: c['qty_available'] for c in outs.product_id.read(['qty_available'])}

        lines = []
        for product in (ins | outs).product_id:
            for out in outs_per_product[product.id]:
                if out.state not in ('partially_available', 'assigned'):
                    continue
                current = currents[out.product_id.id]
                reserved = out.product_uom._compute_quantity(out.reserved_availability, product.uom_id, product.id)
                currents[product.id] -= reserved
                lines.append(self._prepare_report_line(reserved, move_out=out, reservation=True))

            unreconciled_outs = []
            for out in outs_per_product[product.id]:
                # Reconcile with the current stock.
                current = currents[out.product_id.id]
                reserved = 0.0
                if out.state in ('partially_available', 'assigned'):
                    reserved = out.product_uom._compute_quantity(out.reserved_availability, product.uom_id, product.id)
                demand = out.product_qty - reserved
                taken_from_stock = min(demand, current)
                if not float_is_zero(taken_from_stock, precision_rounding=product.uom_id.rounding):
                    currents[product.id] -= taken_from_stock
                    demand -= taken_from_stock
                    lines.append(self._prepare_report_line(taken_from_stock, move_out=out))
                # Reconcile with the ins.
                if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                    demand = _reconcile_out_with_ins(lines, out, ins_per_product[out.product_id.id], demand, only_matching_move_dest=True)
                if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                    unreconciled_outs.append((demand, out))
            if unreconciled_outs:
                for (demand, out) in unreconciled_outs:
                    # Another pass, in case there are some ins linked to a dest move but that still have some quantity available
                    demand = _reconcile_out_with_ins(lines, out, ins_per_product[product.id], demand, only_matching_move_dest=False)
                    if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
                        # Not reconciled
                        lines.append(self._prepare_report_line(demand, move_out=out, replenishment_filled=False))
            # Unused remaining stock.
            free_stock = currents.get(product.id, 0)
            if not float_is_zero(free_stock, precision_rounding=product.uom_id.rounding):
                lines.append(self._prepare_report_line(free_stock, product=product))
            # In moves not used.
            for in_ in ins_per_product[product.id]:
                if float_is_zero(in_['qty'], precision_rounding=product.uom_id.rounding):
                    continue
                lines.append(self._prepare_report_line(in_['qty'], move_in=in_['move']))
        return lines