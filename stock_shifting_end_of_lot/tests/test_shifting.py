# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase
import datetime


class Test(SavepointCase):
    def setUp(self):
        super().setUp()
        conf = self.env["res.config.settings"].create(
            {
                "group_stock_multi_warehouses": True,
                "group_stock_multi_locations": True,
            }
        )
        conf.execute()
        vals = {
            "end_lot_location_id": self.ref("end_lot_location").id,
            "end_lot_picking_type_id": self.env.ref("stock.picking_type_internal").id,
        }
        self.env.ref("stock.picking_type_out").write(vals)
        inventory = self.ref("inventory_move_end_lot")
        inventory.action_validate()
        assert inventory.state == "done"
        assert self.ref("product_4_end_lot1").qty_available == 100
        picking = self.ref("picking_out_end_lot_product")
        assert picking.state == "draft"
        self.picking = picking

    def actions_picking(self):
        self.picking.action_confirm()
        assert self.picking.state == "confirmed"
        self.picking.action_assign()
        assert self.picking.state == "assigned"

    def test_end_lot(self):
        self.actions_picking()
        assert len(self.picking.move_lines) == 3
        pick = self.picking
        assert len(pick.move_line_ids.mapped("lot_id")) == 2
        self.validate_picking(pick)
        assert pick.state == "done"
        # search end_of_lot picking generated when validated pick
        end_lot = self.env["stock.picking"].search(
            [("origin", "ilike", "End of lot from%")], limit=1
        )
        assert len(end_lot.move_lines) == 3
        end_lot.action_confirm()
        end_lot.action_assign()
        assert end_lot.state == "assigned"
        self.validate_picking(end_lot)
        # Check that quantity are the rest of the stock
        self.check_qty("product_4_end_lot1", end_lot, 10)
        assert self.ref("product_4_end_lot1").qty_available == 0
        self.check_qty("product_4_end_lot2", end_lot, 10)
        self.check_qty("product_4_end_lot_no_lot", end_lot, 5)
        assert self.ref("product_4_end_lot1").qty_available == 0

    def add_multi_lots(self):
        self.product_multilot = self.env['product.product'].create({
            'name': 'Lots product',
            'tracking': 'lot',
            'type': 'product',
            'uom_id': self.env.ref("uom.product_uom_unit").id,
        })
        self.lot_1_product_multilot = self.env['stock.production.lot'].create({
            'product_id': self.product_multilot.id,
            'name': 'lot_1_product_multilot'
        })
        self.lot_2_product_multilot = self.env['stock.production.lot'].create({
            'product_id': self.product_multilot.id,
            'name': 'lot_2_product_multilot'
        })
        self.lot_3_product_multilot = self.env['stock.production.lot'].create({
            'product_id': self.product_multilot.id,
            'name': 'lot_3_product_multilot'
        })
        self.inventory = self.env['stock.inventory'].create({
            'name': '3 Lots product in inventory',
            'filter': 'product',
            'product_id': self.product_multilot.id,
        })

        self.inventory.action_start()
        self.inventory.line_ids = [
            (0, 0, {
                'product_id': self.product_multilot.id,
                'prod_lot_id': self.lot_1_product_multilot.id,
                'product_qty': 100,
                'location_id': self.env.ref('stock.stock_location_stock').id,
            }),
            (0, 0, {
                'product_id': self.product_multilot.id,
                'prod_lot_id': self.lot_2_product_multilot.id,
                'product_qty': 200,
                'location_id': self.env.ref('stock.stock_location_stock').id,
            }),
            (0, 0, {
                'product_id': self.product_multilot.id,
                'prod_lot_id': self.lot_3_product_multilot.id,
                'product_qty': 300,
                'location_id': self.env.ref('stock.stock_location_stock').id,
            }),
            ]
        # self.inventory._action_done()
        self.inventory.action_validate()
        assert self.inventory.state == "done"
        assert self.product_multilot.qty_available == 600

        picking2 = self.env['stock.picking'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_lines': [(0, 0, {
                     'name': "lot1 100",
                     'product_id': self.product_multilot.id,
                     'product_uom': self.product_multilot.uom_id.id,
                     'product_uom_qty': 90.0,
                     'picking_type_id': self.env.ref('stock.picking_type_out').id,
                     'location_id': self.env.ref('stock.stock_location_stock').id,
                     'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                     }),
                   (0, 0, {
                     'name': "lot2 200",
                     'product_id': self.product_multilot.id,
                     'product_uom': self.product_multilot.uom_id.id,
                     'product_uom_qty': 190.0,
                     'picking_type_id': self.env.ref('stock.picking_type_out').id,
                     'location_id': self.env.ref('stock.stock_location_stock').id,
                     'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                     }),
                   (0, 0, {
                     'name': "lot3 300",
                     'product_id': self.product_multilot.id,
                     'product_uom': self.product_multilot.uom_id.id,
                     'product_uom_qty': 290.0,
                     'picking_type_id': self.env.ref('stock.picking_type_out').id,
                     'location_id': self.env.ref('stock.stock_location_stock').id,
                     'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                     }),
                 ]
        })
        self.actions_picking()
        self.picking2 = picking2
        return picking2

    def test_multi_end_lot(self):
        self.add_multi_lots()
        pick = self.picking2
        self.validate_picking(pick)
        assert pick.state == "done"
        end_lot_multi = self.env["stock.picking"].search(
            ['&', ("origin", "ilike", "End of lot from%"),
             ("product_id", "=", self.ref("product_4_end_lot2").id)
             ])
        assert len(end_lot_multi.move_lines) == 3
        end_lot_multi.action_confirm()
        end_lot_multi.action_assign()
        assert end_lot_multi.state == "assigned"
        self.validate_picking(end_lot_multi)
        self.check_qty("product_4_end_lot2", end_lot_multi, 10)
        assert self.ref("product_4_end_lot2").qty_available == 0
        assert len(end_lot_multi) == 1

    def validate_picking(self, picking):
        action = picking.button_validate()
        assert len(picking.move_lines) == 3
        wizard = self.env[(action.get("res_model"))].browse(action.get("res_id"))
        wizard.process()

    def check_qty(self, xml_id, picking, qty):
        assert (
            picking.move_lines.filtered(
                lambda s: s.product_id == self.ref(xml_id)
            ).quantity_done
            == qty
        )

    def ref(self, xml_id):
        """shortcut for a local xml"""
        return self.env.ref("stock_shifting_end_of_lot.%s" % xml_id)
