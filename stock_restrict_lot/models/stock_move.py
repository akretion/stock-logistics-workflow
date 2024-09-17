from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import OrderedSet


class StockMove(models.Model):
    _inherit = "stock.move"

    # seems better to not copy this field except when a move is split, because a move
    # can be copied in multiple different occasions and could even be copied with a
    # different product...
    restrict_lot_id = fields.Many2one("stock.lot", string="Restrict Lot", copy=False)

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals["restrict_lot_id"] = self.restrict_lot_id.id
        return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("restrict_lot_id")
        return distinct_fields

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if self.restrict_lot_id:
            if (
                "lot_id" in vals
                and vals["lot_id"] is not False
                and vals["lot_id"] != self.restrict_lot_id.id
            ):
                raise exceptions.UserError(
                    _(
                        "Inconsistencies between reserved quant and lot restriction on "
                        "stock move"
                    )
                )
            vals["lot_id"] = self.restrict_lot_id.id
        return vals

    def _get_available_quantity(
        self,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
        allow_negative=False,
    ):
        self.ensure_one()
        if not lot_id and self.restrict_lot_id:
            lot_id = self.restrict_lot_id
        return super()._get_available_quantity(
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )

    def _update_reserved_quantity(
        self,
        need,
        available_quantity,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        self.ensure_one()
        if self.restrict_lot_id:
            lot_id = self.restrict_lot_id
        return super()._update_reserved_quantity(
            need,
            available_quantity,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _split(self, qty, restrict_partner_id=False):
        vals_list = super()._split(qty, restrict_partner_id=restrict_partner_id)
        if vals_list and self.restrict_lot_id:
            vals_list[0]["restrict_lot_id"] = self.restrict_lot_id.id
        return vals_list

    # Same as _rollup_move_origs but also for "done" moves.
    def _rollup_not_cancelled_move_origs(self, seen=False):
        if not seen:
            seen = OrderedSet()
        for dst in self.move_orig_ids:
            if dst.id not in seen and dst.state != "cancel":
                seen.add(dst.id)
                dst._rollup_move_origs(seen)
        return seen

    def write(self, vals):
        if "restrict_lot_id" not in vals:
            res = super().write(vals)
            if "move_dest_ids" in vals or "move_orig_ids" in vals:
                for move in self:
                    chained_moves = (
                            move | move.get_all_dest_moves() | move.get_all_orig_moves()
                    )
                    if not move.restrict_lot_id and move.state not in ["done", "cancel"]:
                        # update restrict_lot_id on current move from chained_moves
                        if chained_moves.restrict_lot_id:
                            move.restrict_lot_id = chained_moves.restrict_lot_id[0]
                    else:
                        # update chained_moves
                        to_update_move = chained_moves.filtered(
                            lambda sm: sm.state not in ['done', 'cancel'] and
                                       sm.restrict_lot_id != move.restrict_lot_id
                        )
                        to_update_move.restrict_lot_id = move.restrict_lot_id
            else:
                return res
        else:
            restrict_lot_id = vals.pop("restrict_lot_id")
            restrict_lot = self.env["stock.lot"].browse(restrict_lot_id)
            chained_moves = OrderedSet(self)
            self._rollup_move_dests(chained_moves)
            self._rollup_not_cancelled_move_origs(chained_moves)
            if any(
                [
                    sm.state == "done" and sm.lot_ids and sm.lot_ids != restrict_lot
                    for sm in chained_moves
                ]
            ):
                raise ValidationError(
                    _(
                        "You can't modify the Lot/Serial number "
                        "because at least one move in the chain has "
                        "already been done with another Lot/Serial number."
                    )
                )
            super(StockMove, chained_moves).write({"restrict_lot_id": restrict_lot_id})
        return super().write(vals)
