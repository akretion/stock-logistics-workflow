from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    # seems better to not copy this field except when a move is split, because a move
    # can be copied in multiple different occasions and could even be copied with a
    # different product...
    restrict_package_id = fields.Many2one(
        "stock.quant.package", string="Restrict Package", copy=False, index=True
    )

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals["restrict_package_id"] = self.restrict_package_id.id
        return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("restrict_package_id")
        return distinct_fields

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant
        )
        if self.restrict_package_id:
            if (
                "package_id" in vals
                and vals["package_id"] is not False
                and vals["package_id"] != self.restrict_package_id.id
            ):
                raise exceptions.UserError(
                    _(
                        "Inconsistencies between reserved quant and lot restriction on "
                        "stock move"
                    )
                )
            vals["package_id"] = self.restrict_package_id.id
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
        if not package_id and self.restrict_package_id:
            package_id = self.restrict_package_id
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
        if self.restrict_package_id:
            package_id = self.restrict_package_id
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
        if vals_list and self.restrict_package_id:
            vals_list[0]["restrict_package_id"] = self.restrict_package_id.id
        return vals_list

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        self._check_package_consistent_with_restriction()
        return res

    def _check_package_consistent_with_restriction(self):
        """
        Check that the lot set on move lines
        is the same as the restricted lot set on the move
        """
        for move in self:
            if not (move.restrict_package_id and move.move_line_ids):
                continue
            move_line_package = move.mapped("move_line_ids.package_id")
            if move.restrict_package_id != move_line_package:
                raise UserError(
                    _(
                        "The package(s) %(move_line_lot)s being moved is "
                        "inconsistent with the restriction on "
                        "lot %(move_restrict_package)s set on the move",
                        move_line_package=", ".join(
                            move_line_package.mapped("display_name")
                        ),
                        move_restrict_package=move.restrict_package_id.display_name,
                    )
                )
