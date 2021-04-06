from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ProductShortInfo(Datamodel):
    _name = "product.short.info"

    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    code = fields.String(required=False, allow_none=False)
    barcode = fields.String(required=False)
    weight = fields.Float(required=False)
    volume = fields.Float(required=False)
