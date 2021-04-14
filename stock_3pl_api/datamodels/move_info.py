from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class MoveInfo(Datamodel):
    _name = "move.info"

    id = fields.Integer(required=True, allow_none=False)
    product = NestedModel("product.short.info")
    quantity = fields.Float(required=True, allow_none=False)
    quantity_uom = fields.Float(required=True, allow_none=False)
    uom_name = fields.String(required=True, allow_none=False)
    origin = fields.String(required=True, allow_none=False)
    dest = fields.String(required=True, allow_none=False)
    state = fields.String(required=True, allow_none=False)
    id_3pl = fields.String(required=False)
    lines = NestedModel("move.line.info", many=True)
