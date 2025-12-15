from odoo import _, api, exceptions, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    tracking_url = fields.Char(string="Tracking URL", copy=False)

    @api.constrains("name")
    def _constrain_name_unique(self):
        for rec in self:
            if self.search_count([("name", "=", rec.name), ("id", "!=", rec.id)]):
                raise exceptions.UserError(_("Package name must be unique!"))
