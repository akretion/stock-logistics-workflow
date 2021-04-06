# Copyright 2021 AKRETION
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class MoveUpdateParam(Datamodel):
    _name = "move.update.param"

    id = fields.Integer(required=True, allow_none=False)
    scheduled_date = fields.Date(required=False)
    date_done = fields.Date(required=False)
    id_3pl = fields.String(required=False)
    quantity_done = fields.Integer(required=False)
    packages = NestedModel("package.update.param", many=True)
    exception = fields.String(required=False)
