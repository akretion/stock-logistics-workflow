# Copyright 2021 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    id_3pl = fields.Char(
        help="3PL reference id once exported if any",
    )

    # ripped from OCA/wms/shopfloor
    total_weight = fields.Float(
        compute="_compute_picking_info",
        help="Technical field. Indicates total weight of transfers included.",
    )

    @api.depends(
        "move_line_ids", "move_line_ids.product_qty", "move_line_ids.product_id.weight"
    )
    def _compute_picking_info(self):
        for item in self:
            item.update(
                {
                    "total_weight": item._calc_weight(),
                    "move_line_count": len(item.move_line_ids),
                }
            )

    def _calc_weight(self):
        weight = 0.0
        for move_line in self.mapped("move_line_ids"):
            weight += move_line.product_qty * move_line.product_id.weight
        return weight
