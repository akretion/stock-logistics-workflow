from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields += ["restrict_package_id"]
        return fields

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        values = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        values["restrict_package_id"] = (
            move_to_copy.restrict_package_id.id
            if move_to_copy.restrict_package_id
            else False
        )
        return values
