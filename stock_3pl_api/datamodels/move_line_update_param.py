# Copyright 2021 AKRETION
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class MoveLineUpdateParam(Datamodel):
    _name = "move.line.update.param"

    quantity = fields.Integer(required=True, allow_none=False)
    lot_id = fields.String(required=False)
    package = NestedModel("package.update.param")
