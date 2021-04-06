# Copyright 2021 AKRETION
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PickingUpdateParam(Datamodel):
    _name = "picking.update.param"

    scheduled_date = fields.Date(required=False)
    date_done = fields.Date(required=False)
    exception = fields.String(required=False)
    id_3pl = fields.String(required=False)
    moves = NestedModel("move.update.param", many=True)
