from odoo.tests.common import TransactionCase


class TestCancelMovePropagation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        move_vals = {
            "name": "first move",
            "product_id": cls.env.ref("product.product_product_6").id,
            "location_id": cls.env.ref("stock.stock_location_stock").id,
            "location_dest_id": cls.env.ref("stock.stock_location_output").id,
            "product_uom_qty": 50,
            "propagate_cancel": True,
        }
        cls.move1 = cls.env["stock.move"].create(move_vals)
        cls.move1._action_confirm()
        move_vals.update(
            {
                "name": "second move",
                "location_id": cls.env.ref("stock.stock_location_output").id,
                "location_dest_id": cls.env.company.internal_transit_location_id.id,
                "move_orig_ids": [(6, 0, cls.move1.ids)],
            }
        )
        cls.move2 = cls.env["stock.move"].create(move_vals)
        cls.move2._action_confirm()
        move_vals.update(
            {
                "name": "third move",
                "location_id": cls.env.company.internal_transit_location_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_orig_ids": [(6, 0, cls.move2.ids)],
            }
        )
        cls.move3 = cls.env["stock.move"].create(move_vals)
        cls.move3._action_confirm()

    def test_move_cancel_backorder_propagation(self):
        self.move1.write({"quantity_done": 30})
        self.move1._action_done(cancel_backorder=True)
        self.assertEqual(self.move2.product_uom_qty, 20)
        self.assertEqual(self.move2.state, "cancel")
        backorder2 = self.move1.move_dest_ids
        self.assertEqual(backorder2.product_uom_qty, 30)
        self.assertNotEqual(backorder2.state, "cancel")
        self.assertEqual(self.move3.product_uom_qty, 20)
        self.assertEqual(self.move3.state, "cancel")
        backorder3 = backorder2.move_dest_ids
        self.assertEqual(backorder3.product_uom_qty, 30)
        self.assertNotEqual(backorder3.state, "cancel")

    def test_cancel_after_multiple_transfer(self):
        self.move1.write({"quantity_done": 30})
        self.move1._action_done()
        backorder_move1 = self.move1.move_dest_ids.move_orig_ids - self.move1
        self.move2.write({"quantity_done": 20})
        self.move2._action_done()
        backorder_move2 = self.move2.move_dest_ids.move_orig_ids - self.move2
        backorder_move1.write({"quantity_done": 10})
        backorder_move1._action_done(cancel_backorder=True)
        self.assertEqual(backorder_move2.product_uom_qty, 10)
        self.assertEqual(backorder_move2.state, "cancel")
        backorder2 = self.move2.move_dest_ids.move_orig_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
        )
        self.assertEqual(backorder2.product_uom_qty, 20)
        self.assertEqual(self.move3.product_uom_qty, 10)
        self.assertEqual(self.move3.state, "cancel")
        self.assertEqual(backorder2.move_dest_ids.product_uom_qty, 40)

    def test_cancel_with_unmatched_quantity(self):
        self.move2.write({"product_uom_qty": 30})
        self.move1.write({"quantity_done": 30})
        self.move1._action_done(cancel_backorder=True)
        # we keep orig 30 qty, no cancelation happend because total quantity of
        # step 2 was already below the not canceled qty of step 1
        self.assertEqual(self.move2.product_uom_qty, 30)
        self.assertNotEqual(self.move2.state, "cancel")
        self.move2.write({"quantity_done": 20})
        self.move2._action_done(cancel_backorder=True)
        self.assertEqual(self.move3.product_uom_qty, 10)
        self.assertEqual(self.move3.state, "cancel")
