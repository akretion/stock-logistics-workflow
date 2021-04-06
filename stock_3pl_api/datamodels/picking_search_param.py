# Copyright 2021 AKRETION
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PickingSearchParam(Datamodel):
    _name = "picking.search.param"

    picking_type_name = fields.String(required=False)
    states = fields.String(required=False)
    date_from = fields.Date(required=False)
    date_to = fields.Date(required=False)
    id_3pl = fields.String(required=False)
