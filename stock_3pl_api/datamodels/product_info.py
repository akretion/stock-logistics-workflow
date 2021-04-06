from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ProductInfo(Datamodel):
    _name = "product.info"

    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    code = fields.String(required=False, allow_none=False)
    description = fields.String(required=False)
    barcode = fields.String(required=False)
    weight = fields.Float(required=False)
    volume = fields.Float(required=False)
    category_name = fields.String(required=True, allow_none=False)
    uom_name = fields.String(required=True, allow_none=False)
    tracking_type = fields.String(required=True, allow_none=False)
    quantity = fields.Float(required=True, allow_none=False)
    incoming_quantity = fields.Float(required=True, allow_none=False)
    outgoing_quantity = fields.Float(required=True, allow_none=False)
