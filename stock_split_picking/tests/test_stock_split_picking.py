# Copyright 2017 Tecnativa - Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2018 Camptocamp SA - Julien Coux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestStockSplitPicking(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockSplitPicking, cls).setUpClass()

        cls.src_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_id = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "uom_id": cls.uom_id.id}
        )
        cls.product_3 = cls.env["product.product"].create(
            {"name": "Test product 3", "type": "product", "uom_id": cls.uom_id.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.src_location.id,
                "location_dest_id": cls.dest_location.id,
            }
        )
        cls.move = cls.env["stock.move"].create(
            {
                "name": "/",
                "picking_id": cls.picking.id,
                "product_id": cls.product.id,
                "product_uom_qty": 10,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.src_location.id,
                "location_dest_id": cls.dest_location.id,
            }
        )

    def test_stock_split_picking(self):
        # Picking state is draft
        self.assertEqual(self.picking.state, "draft")
        # We can't split a draft picking
        with self.assertRaises(UserError):
            self.picking.split_process("quantity_done")
        # Confirm picking
        self.picking.action_confirm()
        # We can't split an unassigned picking
        with self.assertRaises(UserError):
            self.picking.split_process("quantity_done")
        # We assign quantities in order to split
        self.picking.action_assign()
        move_line = self.env["stock.move.line"].search(
            [("picking_id", "=", self.picking.id)], limit=1
        )
        move_line.qty_done = 4.0
        # Split picking: 4 and 6
        # import pdb; pdb.set_trace()
        self.picking.split_process("quantity_done")

        # We have a picking with 4 units in state assigned
        self.assertAlmostEqual(move_line.qty_done, 4.0)
        self.assertAlmostEqual(move_line.product_qty, 4.0)
        self.assertAlmostEqual(move_line.product_uom_qty, 4.0)

        self.assertAlmostEqual(self.move.quantity_done, 4.0)
        self.assertAlmostEqual(self.move.product_qty, 4.0)
        self.assertAlmostEqual(self.move.product_uom_qty, 4.0)

        self.assertEqual(self.picking.state, "assigned")
        # An another one with 6 units in state assigned
        new_picking = self.env["stock.picking"].search(
            [("backorder_id", "=", self.picking.id)], limit=1
        )
        move_line = self.env["stock.move.line"].search(
            [("picking_id", "=", new_picking.id)], limit=1
        )

        self.assertAlmostEqual(move_line.qty_done, 0.0)
        self.assertAlmostEqual(move_line.product_qty, 6.0)
        self.assertAlmostEqual(move_line.product_uom_qty, 6.0)

        self.assertAlmostEqual(new_picking.move_lines.quantity_done, 0.0)
        self.assertAlmostEqual(new_picking.move_lines.product_qty, 6.0)
        self.assertAlmostEqual(new_picking.move_lines.product_uom_qty, 6.0)

        self.assertEqual(new_picking.state, "assigned")

    def test_stock_split_picking_wizard_move(self):
        self.move2 = self.move.copy()
        self.assertEqual(self.move2.picking_id, self.picking)
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=self.picking.ids)
            .create({"mode": "move"})
        )
        wizard.action_apply()
        self.assertNotEqual(self.move2.picking_id, self.picking)
        self.assertEqual(self.move.picking_id, self.picking)

    def test_stock_split_picking_wizard_avaiable(self):
        stock_move_data = [
            {
                "name": "/",
                "picking_id": self.picking.id,
                "product_id": self.product.id,
                "product_uom_qty": 5,
                "product_uom": self.product.uom_id.id,
                "location_id": self.src_location.id,
                "location_dest_id": self.dest_location.id,
            },
            {
                "name": "/",
                "picking_id": self.picking.id,
                "product_id": self.product_3.id,
                "product_uom_qty": 5,
                "product_uom": self.product_3.uom_id.id,
                "location_id": self.src_location.id,
                "location_dest_id": self.dest_location.id,
            },
        ]
        self.move_ids = self.env["stock.move"].create(stock_move_data)
        self.assertEqual(self.move_ids[0].picking_id, self.picking)
        self.picking.action_confirm()

        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=self.picking.ids)
            .create({"mode": "available_product"})
        )
        wizard.action_apply()

        # self.assertNotEqual(self.move_ids[0].picking_id, self.picking)
        self.assertEqual(self.move.picking_id, self.picking)

    def test_stock_split_picking_wizard_selection(self):
        self.move2 = self.move.copy()
        self.assertEqual(self.move2.picking_id, self.picking)
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=self.picking.ids)
            .create({"mode": "selection", "move_ids": [(6, False, self.move2.ids)]})
        )
        wizard.action_apply()
        self.assertNotEqual(self.move2.picking_id, self.picking)
        self.assertEqual(self.move.picking_id, self.picking)

    def test_stock_picking_split_off_moves(self):
        with self.assertRaises(UserError):
            # fails because we can't split off all lines
            self.picking._split_off_moves(self.picking.move_lines)
        with self.assertRaises(UserError):
            # fails because we can't split cancelled pickings
            self.picking.action_cancel()
            self.picking._split_off_moves(self.picking.move_lines)
