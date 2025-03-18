# Copyright 2025 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    # mimic product_logistics_uom
    # volume and weight with digits=False to accept
    # more precision
    volume = fields.Float(digits=False)
    weight = fields.Float(digits=False)
