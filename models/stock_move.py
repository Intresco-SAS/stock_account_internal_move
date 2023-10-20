# -*- coding: utf-8 -*-
# Copyright (C) 2018 by Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # @override
    # @api.model
    # def _get_valued_types(self):
    #     res = super(StockMove, self)._get_valued_types()
    #     res.append("internal")
    #     return res

    def _get_internal_move_lines(self):
        self.ensure_one()
        res = self.env["stock.move.line"]
        for move_line in self.move_line_ids:
            if (
                move_line.owner_id
                and move_line.owner_id != move_line.company_id.partner_id
            ):
                continue
            if (
                move_line.location_id._should_be_valued()
                and move_line.location_dest_id._should_be_valued()
            ):
                res |= move_line
        return res

    # def _create_internal_svl(self):

    #     svl_vals_list = []
    #     for move in self:
    #         # move = move.with_context(force_company=move.company_id.id)
    #         move = move.with_company(move.company_id)
    #         valued_move_lines = move._get_internal_move_lines()
    #         valued_quantity = 0
    #         for valued_move_line in valued_move_lines:
    #             valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
    #         unit_cost = abs(move._get_price_unit())
    #         if move.product_id.cost_method == "standard":
    #             unit_cost = move.product_id.standard_price
    #         svl_vals = move.product_id._prepare_internal_svl_vals(valued_quantity, move.company_id)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         svl_vals["description"] = move.picking_id.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env["stock.valuation.layer"].sudo().create(svl_vals_list)

    def _action_done(self, cancel_backorder=False):
        """Call _account_entry_move for internal moves as well."""
        res = super(StockMove,self)._action_done(cancel_backorder=False)
        for move in res:
            # first of all, define if we need to even valuate something
            if move.product_id.valuation != 'real_time':
                continue
            # we're customizing behavior on moves between internal locations
            # only, thus ensuring that we don't clash w/ account moves
            # created in `stock_account`
            if not move._is_internal():
                continue
            move.account_entry_move_internal()
        return res
    
    # @override
    def account_entry_move_internal(self):
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return
        if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return 
        
        location_from = self.location_id
        location_to = self.location_dest_id
        resco = list()

        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # get valuation accounts for product
        if self._is_internal():
            stock_valuation = acc_valuation
            stock_journal = journal_id
            cost = self.quantity_done * self.product_id.standard_price
            reference = self.reference
            if self.description_picking:
                reference = reference + " - " + self.description_picking

            if (location_from.force_accounting_entries and location_to.force_accounting_entries):
                resco.append(self.with_company(self.company_id)._prepare_account_move_vals(
                    acc_src,
                    acc_dest,
                    stock_journal,
                    self.quantity_done,
                    reference,
                    False,
                    cost,
                ))
            
            elif location_from.force_accounting_entries:
                resco.append(self.with_company(self.company_id)._prepare_account_move_vals(
                    acc_src,
                    stock_valuation,
                    stock_journal,
                    self.quantity_done,
                    str(self.reference + " - " + self.name),
                    reference,
                    cost,
                ))
            elif location_to.force_accounting_entries:
                resco.append(self.with_company(self.company_id)._prepare_account_move_vals(
                    stock_valuation,
                    acc_dest,
                    stock_journal,
                    self.quantity_done,
                    reference,
                    False,
                    cost,
                ))
            
            account_moves = self.env['account.move'].sudo().create(resco)
            account_moves._post()

        return

    def _is_internal(self):
        self.ensure_one()
        if self._get_internal_move_lines():
            return True
        return False

    def _get_accounting_data_for_valuation(self):
        self.ensure_one()
        (
            journal_id,
            acc_src,
            acc_dest,
            acc_valuation,
        ) = super()._get_accounting_data_for_valuation()
        # intercept account valuation, use account specified on internal
        # location as a local valuation
        if self._is_in() and self.location_dest_id.force_accounting_entries:
            # (acc_src if not dest.usage == 'customer') => acc_valuation
            acc_valuation = self.location_dest_id.valuation_in_account_id.id
        if self._is_out() and self.location_id.force_accounting_entries:
            # acc_valuation => (acc_dest if not dest.usage == 'supplier')
            acc_valuation = self.location_id.valuation_out_account_id.id
        return journal_id, acc_src, acc_dest, acc_valuation
