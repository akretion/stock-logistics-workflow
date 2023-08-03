from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        for move in self:
            if move.propagate_cancel:
                siblings = move.move_dest_ids.mapped("move_orig_ids") - move
                siblings_states = siblings.mapped("state")
                # this is the case of cancel propagation already managed in the stock
                # module
                if all(state == "cancel" for state in siblings_states):
                    continue
                not_cancel_orig_qty = sum(
                    siblings.filtered(lambda m: m.state != "cancel").mapped(
                        "product_qty"
                    )
                )
                not_cancel_dest_qty = sum(
                    # we need to check dest move from orig move because when a move is
                    # split, it looses the link toward done dest move.
                    # the orig moves of an ongoing move always contain all orig though
                    # so we have to check the orig moves of the ongoing dest move of the
                    # move we are canceling.
                    move.move_dest_ids.move_orig_ids.move_dest_ids.filtered(
                        lambda m: m.state != "cancel"
                    ).mapped("product_qty")
                )
                if not_cancel_dest_qty > not_cancel_orig_qty:
                    available_dest_qty_to_cancel = sum(
                        self.move_dest_ids.filtered(
                            lambda m: m.state not in ("done", "cancel")
                        ).mapped("product_qty")
                    )
                    cancelable_dest_qty = min(
                        available_dest_qty_to_cancel,
                        not_cancel_dest_qty - not_cancel_orig_qty,
                    )
                    to_cancel_qty = min(move.product_qty, cancelable_dest_qty)
                    self._propagate_cancel(to_cancel_qty)
        return super()._action_cancel()

    def _propagate_cancel(self, qty):
        self.ensure_one()
        dest_moves = self.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        # Avoid propagating qty if dest moves go in different location because we
        # can't know on which make the propagation.
        if len(dest_moves.location_dest_id) > 1:
            return
        for dest_move in dest_moves:
            if dest_move.product_qty > qty:
                new_move_vals = dest_move._split(dest_move.product_qty - qty)
                new_moves = self.create(new_move_vals)
                new_moves.with_context(bypass_entire_pack=True)._action_confirm(
                    merge=False
                )
            dest_move._action_cancel()
            qty -= dest_move.product_qty
            if qty <= 0:
                break
