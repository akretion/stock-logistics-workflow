# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# Copyright 2018-2021 Jarsa Sistemas (Alan Ramos <alan.ramos@jarsa.com.mx>)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    use_expiry_date = fields.Boolean(related="product_id.use_expiry_date", store=True)
    expiry_date = fields.Date(tracking=True)
    expired = fields.Boolean(compute="_compute_expired", search="_search_expired")

    @api.constrains("use_expiry_date", "expiry_date")
    def _check_use_expiry_date(self):
        for lot in self:
            if lot.use_expiry_date and not lot.expiry_date:
                raise ValidationError(
                    _(
                        "Product %(product)s uses expiry dates, "
                        "but expiry date is missing on lot %(lot)s.",
                        product=lot.product_id.display_name,
                        lot=lot.display_name,
                    )
                )
            elif not lot.use_expiry_date and lot.expiry_date:
                raise ValidationError(
                    _(
                        "Product %(product)s doesn't use expiry dates, "
                        "but an expiry date is set on lot %(lot)s.",
                        product=lot.product_id.display_name,
                        lot=lot.display_name,
                    )
                )

    @api.depends("expiry_date")
    def _compute_expired(self):
        today = fields.Date.context_today(self)
        for lot in self:
            expired = False
            if lot.expiry_date and lot.expiry_date < today:
                expired = True
            lot.expired = expired

    def _search_expired(self, operator, value):
        lot_ids = []
        if operator == "=":
            today = fields.Date.context_today(self)
            domain = [("use_expiry_date", "=", True)]
            if value:
                domain.append(("expiry_date", "<", today))
            else:
                domain.append(("expiry_date", ">=", today))
            lot_ids = list(self._search(domain))
        res = [("id", "in", lot_ids)]
        return res

    @api.depends("name", "expiry_date")
    def name_get(self):
        res = []
        today = fields.Date.context_today(self)
        for lot in self:
            dname = lot.name
            if lot.expiry_date:
                expiry_date_print = format_date(self.env, lot.expiry_date)
                if lot.expiry_date < today:
                    dname = f"[{expiry_date_print} ⚠] {dname}"
                else:
                    dname = "[%s] %s" % (expiry_date_print, dname)
            res.append((lot.id, dname))
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("product_id"):
            product = self.env["product.product"].browse(res["product_id"])
            if (
                product.tracking in ("lot", "serial")
                and product.use_expiry_date
                and product.default_expiry_delay > 0
            ):
                res["expiry_date"] = fields.Date.context_today(self) + timedelta(
                    product.default_expiry_delay
                )
        return res
