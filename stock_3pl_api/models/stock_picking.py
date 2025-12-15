from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    id_3pl = fields.Char(
        help="3PL reference id once exported if any",
    )

    # In V18, we might not need to override _add_delivery_cost_to_so
    # if the context handling is done right in the router,
    # but keeping it safe if specific logic existed.
