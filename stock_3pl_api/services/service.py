from odoo.addons.component.core import AbstractComponent


class BaseStock3plApiService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.stock.3pl.api.service"
    _collection = "stock.3pl.api.service"
    _expose_model = None
