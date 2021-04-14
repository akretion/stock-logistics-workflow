from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PickingInfo(Datamodel):
    _name = "picking.info"

    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    origin = fields.String(required=False)
    partner = NestedModel("partner.info", allow_none=True)
    picking_type_name = fields.String(required=False, allow_none=True)
    state = fields.String(required=True, allow_none=False)
    scheduled_date = fields.Date(required=True, allow_none=False)
    id_3pl = fields.String(required=True, allow_none=False)
    moves = NestedModel("move.info", many=True)
    backorder_id = fields.Integer(required=False)
    backorder_ids = fields.List(fields.Integer())
