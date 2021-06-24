from odoo import _
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.models import expression


class PickingService(Component):
    """
    examples:
    curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/picking
    curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/picking/7
    """
    _inherit = 'base.stock.3pl.api.service'
    _name = 'base.stock.3pl.api.picking'
    _usage = 'picking'
    _collection = 'stock.3pl.api.service'
    _description = "List incoming and outgoing pickings and allow to confirm them"

    @restapi.method(
        [(["/"], "GET")],
        input_param=Datamodel("picking.search.param"),
        output_param=Datamodel("picking.info", is_list=True),
        auth="api_key",
    )
    def search(self, picking_search_param):
        """
        Search pickings
        curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/picking
        curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/picking/7
        curl -H "api_key: key1" \
        "http://localhost:8069/stock_3pl_api/picking?picking_type_name=Receipts"
        curl -H "api_key: key1" \
        "http://localhost:8069/stock_3pl_api/picking\
        ?picking_type_name=Delivery%20Orders&states=confirmed|assigned"
        """
        domain = []
        if picking_search_param.picking_type_id:
            domain = expression.AND(
                [domain, [('picking_type_id', '=', picking_search_param.picking_type_id)]]
            )
        elif picking_search_param.picking_type_name:
            domain = expression.AND(
                [domain, [('picking_type_id', 'ilike', picking_search_param.picking_type_name)]]
            )
        if picking_search_param.origin:
            domain = expression.AND(
                [domain, [('origin', 'ilike', picking_search_param.origin)]]
            )
        if picking_search_param.states:
            if '|' in picking_search_param.states:
                states = picking_search_param.states.split("|")
            else:
                states = [picking_search_param.states]
            domain = expression.AND(
                [domain, [('state', 'in', states)]]
            )
        if picking_search_param.date_from:
            domain = expression.AND(
                [domain, [('scheduled_date', '>', picking_search_param.date_from)]]
            )
        if picking_search_param.date_to:
            domain = expression.AND(
                [domain, [('scheduled_date', '<', picking_search_param.date_to)]]
            )
        if picking_search_param.id_3pl:
            if picking_search_param.id_3pl.lower() == "false":
                domain = expression.AND(
                    [domain, [('id_3pl', '=', False)]]
                )
            elif picking_search_param.id_3pl.lower() == "*":
                domain = expression.AND(
                    [domain, [('id_3pl', '!=', False)]]
                )
            else:
                domain = expression.AND(
                    [domain, [('id_3pl', '=', picking_search_param.id_3pl)]]
                )
        res = []
        for p in self.env["stock.picking"].search(domain):
            res.append(self._to_picking_info(p))
        return res

    @restapi.method(
        [(["/<int:id>"], "GET")],
        output_param=Datamodel("picking.info"),
        auth="api_key",
    )
    def get(self, _id):
        """
        Get picking information
        """
        picking = self.env["stock.picking"].browse(_id)
        return self._to_picking_info(picking)

    @restapi.method(
        [(["/<int:id>"], "POST")],
        input_param=restapi.Datamodel("picking.update.param"),
        output_param=restapi.Datamodel("picking.info"),
        auth="api_key",
    )
    def update(self, _id, picking_update_param):
        """
        Update picking information
        """
        picking = self.env["stock.picking"].browse(_id)
        if picking_update_param.moves:
            for move_update_param in picking_update_param.moves:
                if move_update_param.id not in\
                        picking.move_ids_without_package.mapped("id"):
                    raise ValidationError(
                        _("Move %s doesn't belong to picking %s!")
                        % (move_update_param.id, _id)
                    )
                self._update_move(move_update_param)
        write_dict = self._prepare_picking_write(picking_update_param)
        if write_dict:
            picking.write(write_dict)
        return self._to_picking_info(picking)

    def _prepare_picking_write(self, picking_update_param):
        write_dict = {}
        for key in ["scheduled_date", "date_done", "exception", "id_3pl"]:
            if getattr(picking_update_param, key):
                write_dict[key] = getattr(picking_update_param, key)
        return write_dict

    def _update_move(self, move_update_param):
        move = self.env["stock.move"].browse(move_update_param.id)
        move.move_line_ids.unlink()

        # moves with stock.move.line details
        if move_update_param.lines:
            for line_param in move_update_param.lines:
                if line_param.package:
                    package = self.env['stock.quant.package'].search(
                        [('name', '=', line_param.package.ref)], limit=1
                    )  # (we have a unique name constraint)
                    if package:
                        package.name = line_param.package.ref
                        package.shipping_weight = line_param.package.weight
                        package.tracking_url = line_param.package.tracking_url
                    else:
                        package = self.env['stock.quant.package'].create(
                            {
                                'name': line_param.package.ref,
                                'shipping_weight': line_param.package.weight,
                                'tracking_url': line_param.package.tracking_url,
                            }
                        )
                else:
                    package = None
                self.env['stock.move.line'].create(
                    {
                        'move_id': move.id,
                        'picking_id': move.picking_id.id,
                        'product_id': move.product_id.id,
                        'qty_done': line_param.quantity,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'result_package_id': package.id if package else False,
                        # TODO search lot_id or create it
                    }
                )

        # stock.move.line with no detailed info:
        elif move_update_param.quantity_done:
            self.env['stock.move.line'].create(
                {
                    'move_id': move.id,
                    'picking_id': move.picking_id.id,
                    'product_id': move.product_id.id,
                    'qty_done': move_update_param.quantity_done,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                }
            )

    @restapi.method(
        [(["/<int:id>/done"], "POST")],
        input_param=restapi.Datamodel("picking.done.param"),
        output_param=restapi.Datamodel("picking.info"),
        auth="api_key",
    )
    def done(self, _id, picking_done_param):
        """Set the stock picking to done
        With the qty_done on each move or the reserved quantity if not specified
        """
        picking = self.env["stock.picking"].browse(_id)
        self.update(_id, picking_done_param)
        if picking.state == 'draft':
            picking.action_confirm()
            if picking.state != 'assigned':
                picking.action_assign()
                if picking.state != 'assigned':
                    pass
                    # TODO inform about sonme exception?
                    # if you work only with assigned pickings
                    # such cases should not happen.

        if picking_done_param.force_reserved_quantities:
            for move in picking.move_lines.filtered(
                        lambda m: m.state not in ['done', 'cancel']
                    ):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

        picking.action_done()

        if picking_done_param.cancel_backorder:
            backorder = self.env['stock.picking'].search(
                [('backorder_id', '=', picking.id)],
            )
            backorder.action_cancel()
            picking.message_post(
                body=_("Back order <em>%s</em> <b>cancelled</b>.")
                % (",".join([b.name or '' for b in backorder]))
            )
        return self._to_picking_info(picking)

    def _to_picking_info(self, picking):
        PickingInfo = self.env.datamodels["picking.info"]
        picking_info = PickingInfo(partial=True)
        picking_info.id = picking.id
        picking_info.name = picking.name
        picking_info.origin = picking.origin
        picking_info.partner = self._to_partner_info(picking.partner_id)
        picking_info.picking_type_name = picking.picking_type_id.name
        picking_info.state = picking.state
        picking_info.scheduled_date = picking.scheduled_date
        picking_info.id_3pl = picking.id_3pl or ""
        picking_info.moves = [
            self._to_move_info(m) for m in picking.move_ids_without_package
        ]
        if picking.backorder_id:
            picking_info.backorder_id = picking.backorder_id.id
        picking_info.backorder_ids = picking.backorder_ids.mapped('id')
        return picking_info

    def _to_partner_info(self, partner):
        if not partner:
            return None
        PartnerInfo = self.env.datamodels["3pl.partner.info"]
        partner_info = PartnerInfo(partial=True)
        partner_info.id = partner.id
        partner_info.name = partner.name
        partner_info.email = partner.email or ""
        partner_info.street = partner.street or ""
        partner_info.street2 = partner.street2 or ""
        partner_info.zip_code = partner.zip or ""
        partner_info.city = partner.city or ""
        partner_info.phone = partner.phone or ""
        partner_info.mobile = partner.mobile or ""
        if partner.country_id:
            partner_info.country_code = partner.country_id.code
        if partner.state_id:
            partner_info.state_name = partner.state_id.name
        partner_info.is_company = partner.is_company
        return partner_info

    def _to_move_info(self, move):
        MoveInfo = self.env.datamodels["move.info"]
        move_info = MoveInfo(partial=True)
        move_info.id = move.id
        move_info.product = self._to_product_short_info(move.product_id)
        move_info.quantity = move.product_qty
        move_info.quantity_uom = move.product_uom_qty
        move_info.uom_name = move.product_uom.name
        move_info.origin = move.location_id.name
        move_info.dest = move.location_dest_id.name
        move_info.state = move.state
        move_info.lines = [
            self._to_move_line_info(line) for line in move.move_line_ids
        ]
        return move_info

    def _to_move_line_info(self, move_line):
        MoveLineInfo = self.env.datamodels["move.line.info"]
        line_info = MoveLineInfo(partial=True)
        line_info.id = move_line.id
        line_info.quantity = move_line.qty_done
        line_info.reserved_quantity = move_line.product_uom_qty
        line_info.lot = move_line.lot_name or ""
        if move_line.result_package_id:
            line_info.package_ref = move_line.result_package_id.name
            line_info.package_tracking_url = move_line.result_package_id.tracking_url
        return line_info

    def _to_product_short_info(self, product):
        ProductShortInfo = self.env.datamodels["product.short.info"]
        product_short_info = ProductShortInfo(partial=True)
        product_short_info.id = product.id
        product_short_info.name = product.name
        product_short_info.code = product.default_code
        product_short_info.barcode = product.barcode or ""
        product_short_info.weight = product.weight
        product_short_info.volume = product.volume
        return product_short_info
