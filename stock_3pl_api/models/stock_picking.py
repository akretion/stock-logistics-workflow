# Copyright 2021 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    id_3pl = fields.Char(
        help="3PL reference id once exported if any",
    )

    def _add_delivery_cost_to_so(self):
        pass  # with the API we don't want to alter the SO
