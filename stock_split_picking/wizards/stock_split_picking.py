# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockSplitPicking(models.TransientModel):
    _name = "stock.split.picking"
    _description = "Split a picking"

    mode = fields.Selection(
        [
            ("reserved_quantity", "Reserved quantities"),
            ("move", "One picking per move"),
            ("selection", "Select move lines to split off"),
            ("manual_quantity", "Manual quantities"),
        ],
        required=True,
        default="reserved_quantity",
    )

    picking_ids = fields.Many2many(
        "stock.picking",
        default=lambda self: self._default_picking_ids(),
    )
    move_ids = fields.Many2many("stock.move")

    def _default_picking_ids(self):
        return self.env["stock.picking"].browse(self.env.context.get("active_ids", []))

    def action_apply(self):
        new_pickings = self._action_apply()
        return self._picking_action(new_pickings)

    def _action_apply(self):
        return getattr(self, f"_apply_{self[:1].mode}")()

    def _check_can_split_by_quantity(self):
        for picking in self.picking_ids:
            if all(
                float_is_zero(m.quantity, precision_rounding=m.product_uom.rounding)
                for m in picking.move_ids
            ):
                raise UserError(
                    self.env._(
                        "%s: Nothing to split. Fill the quantities you want in a new "
                        "transfer in the done quantities",
                        picking.display_name,
                    )
                )
            if all(
                float_compare(
                    m.quantity,
                    m.product_uom_qty,
                    precision_rounding=m.product_uom.rounding,
                )
                >= 0
                for m in picking.move_ids
            ):
                raise UserError(
                    self.env._(
                        "%s: Nothing to split, all demand is done. For split you need "
                        "at least one line not fully fulfilled",
                        picking.display_name,
                    )
                )

    def _check_can_split_manual_quantity(self):
        """Check that a quantity to split has been entered on the moves."""
        for picking in self.picking_ids:
            moves = picking.move_ids.filtered(
                lambda move: move.state not in ("done", "cancel")
            )
            for move in moves:
                if (
                    float_compare(
                        move.split_manual_quantity,
                        0.0,
                        precision_rounding=move.product_uom.rounding,
                    )
                    < 0
                ):
                    raise UserError(
                        self.env._(
                            "%(move)s: The quantity to split cannot be negative.",
                            move=move.display_name,
                        )
                    )
            if not any(
                float_compare(
                    move.split_manual_quantity,
                    0.0,
                    precision_rounding=move.product_uom.rounding,
                )
                > 0
                for move in moves
            ):
                raise UserError(
                    self.env._(
                        "%s: Nothing to split. Fill the quantities to split in "
                        "the 'Quantity to Split' column of the operations.",
                        picking.display_name,
                    )
                )

    def _apply_reserved_quantity(self):
        """Apply mode `reserved_quantity`: Split pickings by reserved quantity

        Done quantities will be moved to a new picking, the remaining pending
        moves will stay in the original picking.

        This is similar to the core method `action_split_transfer`, with one important
        difference: the core method keeps the assigned quantities in the original record
        and creates a backorder for the remaining quantities. This method, on the other
        hand, extracts the selected quantities in a new picking, and keeps the original
        one as backorder.
        """
        self._check_can_split_by_quantity()
        new_pickings = self.env["stock.picking"]
        for picking in self.picking_ids:
            new_moves_vals = []
            moves_to_split_off = self.env["stock.move"]
            moves_to_recompute_state = self.env["stock.move"]
            for move in picking.move_ids:
                rounding = move.product_uom.rounding
                # Do not split moves that are done or cancelled
                if move.state in ("done", "cancel"):
                    continue
                # If there aren't assigned quantities, there's nothing to split
                if float_is_zero(move.quantity, precision_rounding=rounding):
                    continue
                # If it's completely assigned, extract the move entirely
                if (
                    float_compare(
                        move.quantity, move.product_uom_qty, precision_rounding=rounding
                    )
                    >= 0
                ):
                    moves_to_split_off += move
                    continue
                # Otherwise, we split the done quantities and leave the remaining
                # quantities in the original move.
                split_moves_vals = move.with_context(cancel_backorder=False)._split(
                    move.product_uom._compute_quantity(
                        move.quantity, move.product_id.uom_id, rounding_method="HALF-UP"
                    )
                )
                if not split_moves_vals:
                    continue  # pragma: no cover
                # Adopt the move lines from the original move
                split_moves_vals[0]["move_line_ids"] = [
                    Command.set(move.move_line_ids.ids)
                ]
                new_moves_vals += split_moves_vals
                moves_to_recompute_state += move
            # Create the partially split off moves
            if new_moves_vals:
                new_moves = self.env["stock.move"].create(new_moves_vals)
                new_moves.with_context(
                    bypass_entire_pack=True, bypass_procurement_creation=True
                )._action_confirm(merge=False)
                moves_to_split_off += new_moves
            # Recompute the state of the remaining moves
            moves_to_recompute_state._recompute_state()
            # If all the picking moves are the ones to be split, then it means
            # we haven't created any backorder move. We keep the picking as-is.
            if picking.move_ids == moves_to_split_off or not moves_to_split_off:
                continue  # pragma: no cover
            # Create the split orders for the extracted moves, and split them off
            new_pickings += picking._split_off_moves(moves_to_split_off)
        return new_pickings

    def _apply_move(self):
        """Apply mode `mode`: One picking per move

        Extract the first move from the picking and move it to a new one.
        Keep the rest in the original picking.
        """
        new_pickings = self.env["stock.picking"]
        for picking in self.picking_ids:
            # If the picking only has one move, there's nothing to split
            if len(picking.move_ids) <= 1:
                continue
            # Get the moves that can be split off (not done nor cancelled)
            todo = picking.move_ids.filtered(
                lambda move: move.state not in ("done", "cancel")
            ).sorted()
            if not todo:
                continue
            # Split off the first one
            new_pickings += picking._split_off_moves(todo[0])
        return new_pickings

    def _apply_selection(self):
        """Apply mode `selection`: Split off selected moves"""
        moves = self.mapped("move_ids")
        new_picking = moves.mapped("picking_id")._split_off_moves(moves)
        return new_picking

    def _apply_manual_quantity(self):
        """Apply mode `manual_quantity`: Split pickings by manual quantity

        The quantity entered on each move in the field `split_manual_quantity`
        is extracted in a new picking, the rest of the demand stays in the
        original picking. This is the same mechanism as the
        `reserved_quantity` mode, except that the quantity to extract is the
        one typed by the user instead of the reserved quantity.

        The reservation follows the extracted quantity only when it is exactly
        the reserved quantity of the move. Otherwise the reservation of the
        move left in the original picking is released when it exceeds the
        remaining demand, and the new picking is reserved again: both pickings
        stay consistent and can be processed.
        """
        self._check_can_split_manual_quantity()
        new_pickings = self.env["stock.picking"]
        for picking in self.picking_ids:
            new_moves_vals = []
            moves_to_split_off = self.env["stock.move"]
            moves_to_recompute_state = self.env["stock.move"]
            for move in picking.move_ids:
                rounding = move.product_uom.rounding
                # Do not split moves that are done or cancelled
                if move.state in ("done", "cancel"):
                    continue
                manual_qty = move.split_manual_quantity
                if float_is_zero(manual_qty, precision_rounding=rounding):
                    continue
                # If the quantity to split covers the whole demand, extract the
                # move entirely
                if (
                    float_compare(
                        manual_qty,
                        move.product_uom_qty,
                        precision_rounding=rounding,
                    )
                    >= 0
                ):
                    moves_to_split_off += move
                    continue
                # Otherwise, extract the quantity to split in a new move and
                # leave the remaining demand in the original move
                split_moves_vals = move.with_context(cancel_backorder=False)._split(
                    move.product_uom._compute_quantity(
                        manual_qty,
                        move.product_id.uom_id,
                        rounding_method="HALF-UP",
                    )
                )
                if not split_moves_vals:
                    continue  # pragma: no cover
                # The reservation goes with the extracted move only when the
                # quantity to split is exactly the reserved quantity: the
                # reserved move lines would not match the extracted demand
                # otherwise.
                if not float_compare(
                    manual_qty, move.quantity, precision_rounding=rounding
                ):
                    split_moves_vals[0]["move_line_ids"] = [
                        Command.set(move.move_line_ids.ids)
                    ]
                new_moves_vals += split_moves_vals
                moves_to_recompute_state += move
            # Create the partially split off moves
            if new_moves_vals:
                new_moves = self.env["stock.move"].create(new_moves_vals)
                new_moves.with_context(
                    bypass_entire_pack=True, bypass_procurement_creation=True
                )._action_confirm(merge=False)
                # The extracted moves can carry the reservation of the original
                # moves: recompute their state so that they are 'assigned' as
                # soon as they are fully reserved (the confirmation of a move
                # linked to a picking does not reserve anything).
                new_moves._recompute_state()
                moves_to_split_off += new_moves
            # Recompute the state of the remaining moves
            moves_to_recompute_state._recompute_state()
            # If all the picking moves are the ones to be split, then it means
            # we haven't created any backorder move. We keep the picking as-is.
            if picking.move_ids == moves_to_split_off or not moves_to_split_off:
                continue
            new_picking = picking._split_off_moves(moves_to_split_off)
            new_pickings += new_picking
            # The moves left in the original picking can keep a reservation
            # bigger than their remaining demand: release it, then reserve the
            # new picking.
            over_reserved_moves = moves_to_recompute_state.filtered(
                lambda m: float_compare(
                    m.quantity,
                    m.product_uom_qty,
                    precision_rounding=m.product_uom.rounding,
                )
                > 0
            )
            if over_reserved_moves:
                over_reserved_moves._do_unreserve()
                new_picking.action_assign()
        return new_pickings

    def _picking_action(self, pickings):
        if not pickings:
            return True
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all",
        )
        action["domain"] = [("id", "in", pickings.ids)]
        return action
