from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class MoveLineInfo(Datamodel):
    _name = "move.line.info"

    id = fields.Integer(required=True, allow_none=False)
    quantity = fields.Float(required=True)
    reserved_quantity = fields.Float(required=False)
    lot = fields.String(required=False)
    package_ref = fields.String(required=False)
    package_tracking_url = fields.String(required=False)
