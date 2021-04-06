# Copyright 2021 Akretion
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.base_rest.controllers import main


class Stock3PLApiController(main.RestController):
    _root_path = "/stock-3pl-api/"
    _collection_name = "stock.3pl.api.service"
    _default_auth = "api_key"
