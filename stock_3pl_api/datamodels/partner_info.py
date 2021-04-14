# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PartnerInfo(Datamodel):
    _name = "3pl.partner.info"

    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    street = fields.String(required=True, allow_none=False)
    street2 = fields.String(required=False, allow_none=True)
    zip_code = fields.String(required=True, allow_none=False)
    city = fields.String(required=True, allow_none=False)
    phone = fields.String(required=False)
    state_name = fields.String(required=False)
    country_name = fields.String(required=False)
    is_company = fields.Boolean(required=False)
