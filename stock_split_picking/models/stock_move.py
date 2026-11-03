# Copyright 2026 Akretion
# @author Benoît Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    split_manual_quantity = fields.Float(
        string="Quantity to Split",
        digits="Product Unit of Measure",
        copy=False,
        help="Quantity of this move to extract in a new transfer when the "
        "picking is split with the mode 'Manual quantities'. The rest of the "
        "demand stays in the original transfer.",
    )
