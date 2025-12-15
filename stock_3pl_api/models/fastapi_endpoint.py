from odoo import fields, models

from ..routers import stock_3pl_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app = fields.Selection(
        selection_add=[("stock_3pl", "Stock 3PL API")],
        ondelete={"stock_3pl": "cascade"},
    )

    def _get_fastapi_routers(self):
        if self.app == "stock_3pl":
            return [stock_3pl_router]
        return super()._get_fastapi_routers()
