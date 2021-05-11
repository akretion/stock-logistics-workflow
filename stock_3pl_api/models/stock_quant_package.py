# Copyright 2021 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, exceptions, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    # tracking_ref = fields.Char(string='Tracking Reference', copy=False)
    # we assume the tracking ref is set in the name directly
    tracking_url = fields.Char(string='Tracking URL', copy=False)

    # ripped from OCA/wms/shopfloor
    @api.constrains("name")
    def _constrain_name_unique(self):
        for rec in self:
            if self.search_count([("name", "=", rec.name), ("id", "!=", rec.id)]):
                raise exceptions.UserError(_("Package name must be unique!"))
