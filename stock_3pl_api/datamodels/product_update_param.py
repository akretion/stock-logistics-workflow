# Copyright 2021 AKRETION
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ProductUpdateParam(Datamodel):
    _name = "product.update.param"

    location_name = fields.String()
    location_id = fields.Integer()
    new_quantity = fields.Float()
    delta_quantity = fields.Float()
