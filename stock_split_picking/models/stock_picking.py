# Copyright 2013-2015 Camptocamp SA - Nicolas Bessi
# Copyright 2018 Camptocamp SA - Julien Coux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    """Adds picking split without done state."""

    _inherit = "stock.picking"

    def _check_split_process(self, split_move_type):
        # Check the picking state and condition before split
        if self.state == "draft":
            raise UserError(_("Mark as todo this picking please."))

        if split_move_type == "quantity_done":
            if all([x.qty_done == 0.0 for x in self.move_line_ids]):
                raise UserError(
                    _(
                        "You must enter done quantity in order to split your "
                        "picking in several ones."
                    )
                )

    def split_process(self, split_move_type):
        """Use to trigger the wizard from button with correct context"""
        for picking in self:
            picking._check_split_process(split_move_type)

            # Split moves considering the qty_done on moves
            new_moves = self.env["stock.move"]
            for move in picking.move_lines:
                rounding = move.product_uom.rounding
                qty_compare_split = getattr(move, split_move_type)
                qty_initial = move.product_uom_qty
                qty_diff_compare = float_compare(
                    qty_compare_split, qty_initial, precision_rounding=rounding
                )
                if qty_diff_compare < 0:
                    qty_split = qty_initial - qty_compare_split
                    qty_uom_split = move.product_uom._compute_quantity(
                        qty_split, move.product_id.uom_id, rounding_method="HALF-UP"
                    )
                    new_move_vals = move._split(qty_uom_split)
                    if new_move_vals:
                        for move_line in move.move_line_ids:
                            if move_line.product_qty and move_line.qty_done:
                                # To avoid an error
                                # when picking is partially available
                                try:
                                    move_line.write(
                                        {"product_uom_qty": move_line.qty_done}
                                    )
                                except UserError:
                                    pass
                        new_move = self.env["stock.move"].create(new_move_vals)
                    else:
                        new_move = move
                    new_move._action_confirm(merge=False)
                    new_moves |= new_move

            # If we have new moves to move, create the backorder picking
            if new_moves:
                backorder_picking = picking._create_split_backorder()
                new_moves.write({"picking_id": backorder_picking.id})
                new_moves.move_line_ids.write({"picking_id": backorder_picking.id})
                new_moves._action_assign()

    def _create_split_backorder(self, default=None):
        """Copy current picking with defaults passed, post message about
        backorder"""
        self.ensure_one()
        backorder_picking = self.copy(
            dict(
                {
                    "name": "/",
                    "move_lines": [],
                    "move_line_ids": [],
                    "backorder_id": self.id,
                },
                **(default or {})
            )
        )
        self.message_post(
            body=_(
                'The backorder <a href="#" '
                'data-oe-model="stock.picking" '
                'data-oe-id="%d">%s</a> has been created.'
            )
            % (backorder_picking.id, backorder_picking.name)
        )
        return backorder_picking

    def _split_off_moves(self, moves):
        """Remove moves from pickings in self and put them into a new one"""
        new_picking = self.env["stock.picking"]
        for this in self:
            if this.state in ("done", "cancel"):
                raise UserError(
                    _("Cannot split picking %s in state %s")
                    % (
                        this.name,
                        this.state,
                    )
                )
            new_picking = new_picking or this._create_split_backorder()
            if not this.move_lines - moves:
                raise UserError(
                    _("Cannot split off all moves from picking %s") % this.name
                )
        moves.write({"picking_id": new_picking.id})
        moves.move_line_ids.write({"picking_id": new_picking.id})

        return new_picking

    def _split_product_quantities(self, moves, split_list):
        new_picking = self.env["stock.picking"]
        for this in self:
            if this.state in ("done", "cancel"):
                raise UserError(
                    _("Cannot split picking %s in state %s")
                    % (
                        this.name,
                        this.state,
                    )
                )
            new_picking = new_picking or this._create_split_backorder()
        for record in split_list:
            move_id = moves.filtered(lambda r: r.product_id == record["product_id"])
            if record["qty"] == move_id.product_uom_qty:
                move_id.write({"picking_id": new_picking.id})
                move_id.move_line_ids.write({"picking_id": new_picking.id})
            elif record["qty"] < move_id.product_uom_qty:
                new_move_id = move_id.copy()
                move_id.product_uom_qty -= record["qty"]
                new_move_id.write(
                    {"picking_id": new_picking.id, "product_uom_qty": record["qty"]}
                )
                new_move_id.move_line_ids.write({"picking_id": new_picking.id})
                new_move_id.action_confirm()
                new_move_id.action_assing()
