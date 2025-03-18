# Copyright 2025 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import tagged

from odoo.addons.stock_landed_costs.tests.common import TestStockLandedCostsCommon


@tagged("post_install", "-at_install")
class TestStockLandedCosts(TestStockLandedCostsCommon):
    def test_stock_landed_costs_1dm3(self):
        # put in a picking the same qty of product 1 and product 2
        # product 1 is dm³ and product 2 is 9dm³
        # we ensure the volume is not rounded at 0
        # if volume rounded at 0 then no landed cost apply
        # here we assume m³ for readabilty
        # it's the same with imperial units

        # basic conversion
        # ** = power operator
        one_dm3_in_m3 = 0.1**3
        nine_dm3_in_dm3 = one_dm3_in_m3 * 9

        product_1 = self.env["product.product"].create(
            {
                "name": "Product 1",
                "weight": 20,
                "volume": one_dm3_in_m3,  # 1dm³ in m³
                "categ_id": self.stock_account_product_categ.id,
                "type": "product",
            }
        )

        product_2 = self.env["product.product"].create(
            {
                "name": "Product 2",
                "weight": 20,
                "volume": nine_dm3_in_dm3,
                "categ_id": self.stock_account_product_categ.id,
                "type": "product",
            }
        )

        self.assertEqual(product_1.value_svl, 0)
        self.assertEqual(product_1.quantity_svl, 0)
        self.assertEqual(product_2.value_svl, 0)
        self.assertEqual(product_2.quantity_svl, 0)

        picking_default_vals = self.env["stock.picking"].default_get(
            list(self.env["stock.picking"].fields_get())
        )

        vals = dict(
            picking_default_vals,
            **{
                "name": "LC pick",
                "picking_type_id": self.warehouse.in_type_id.id,
                "location_id": self.supplier_location_id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product_1.name,
                            "product_id": product_1.id,
                            "product_uom_qty": 1,
                            "product_uom": self.ref("uom.product_uom_unit"),
                            "location_id": self.supplier_location_id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": product_2.name,
                            "product_id": product_2.id,
                            "product_uom_qty": 1,
                            "product_uom": self.ref("uom.product_uom_unit"),
                            "location_id": self.supplier_location_id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                        },
                    ),
                ],
            }
        )

        picking_landed_cost = self.env["stock.picking"].create(vals)

        picking_landed_cost.action_confirm()
        for m in picking_landed_cost.move_lines:
            m.quantity_done = m.product_uom_qty
        picking_landed_cost.button_validate()

        self.assertEqual(product_1.value_svl, 0)
        self.assertAlmostEqual(product_1.quantity_svl, 1)
        self.assertEqual(product_2.value_svl, 0)
        self.assertAlmostEqual(product_2.quantity_svl, 1)

        lc_by_volume = self.env["product.product"].create(
            {
                "name": "Landed cost by volume",
                "categ_id": self.stock_account_product_categ.id,
            }
        )
        default_vals = self.env["stock.landed.cost"].default_get(
            list(self.env["stock.landed.cost"].fields_get())
        )

        default_vals.update(
            {
                "picking_ids": [picking_landed_cost.id],
                "account_journal_id": self.expenses_journal.id,
                "cost_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "by volume",
                            "product_id": lc_by_volume.id,
                            "split_method": "by_volume",
                            "price_unit": 100,
                        },
                    )
                ],
                "valuation_adjustment_lines": [],
            }
        )
        stock_landed_cost_1 = self.env["stock.landed.cost"].create(default_vals)

        stock_landed_cost_1.compute_landed_cost()

        l1, l2 = stock_landed_cost_1.valuation_adjustment_lines
        self.assertAlmostEqual(l1.volume, 0.001)
        self.assertAlmostEqual(l2.volume, 0.009)
        self.assertEqual(l1.additional_landed_cost + l2.additional_landed_cost, 100)

    def test_stock_landed_costs_weight(self):
        # put in a picking a product with a really small weight
        # withtout this module the additionnal_landed_cost will be 0
        # basic conversion
        one_gram_in_kg = 0.0001

        product_1 = self.env["product.product"].create(
            {
                "name": "Product 1",
                "weight": one_gram_in_kg,
                "volume": 1,
                "categ_id": self.stock_account_product_categ.id,
                "type": "product",
            }
        )

        self.assertEqual(product_1.value_svl, 0)
        self.assertEqual(product_1.quantity_svl, 0)

        picking_default_vals = self.env["stock.picking"].default_get(
            list(self.env["stock.picking"].fields_get())
        )

        vals = dict(
            picking_default_vals,
            **{
                "name": "LC pick",
                "picking_type_id": self.warehouse.in_type_id.id,
                "location_id": self.supplier_location_id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product_1.name,
                            "product_id": product_1.id,
                            "product_uom_qty": 1,
                            "product_uom": self.ref("uom.product_uom_unit"),
                            "location_id": self.supplier_location_id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                        },
                    ),
                ],
            }
        )

        picking_landed_cost = self.env["stock.picking"].create(vals)

        picking_landed_cost.action_confirm()
        for m in picking_landed_cost.move_lines:
            m.quantity_done = m.product_uom_qty
        picking_landed_cost.button_validate()

        self.assertEqual(product_1.value_svl, 0)
        self.assertAlmostEqual(product_1.quantity_svl, 1)

        lc_by_weight = self.env["product.product"].create(
            {
                "name": "Landed cost by weight",
                "categ_id": self.stock_account_product_categ.id,
            }
        )
        default_vals = self.env["stock.landed.cost"].default_get(
            list(self.env["stock.landed.cost"].fields_get())
        )

        default_vals.update(
            {
                "picking_ids": [picking_landed_cost.id],
                "account_journal_id": self.expenses_journal.id,
                "cost_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "by volume",
                            "product_id": lc_by_weight.id,
                            "split_method": "by_weight",
                            "price_unit": 100,
                        },
                    )
                ],
                "valuation_adjustment_lines": [],
            }
        )
        stock_landed_cost_1 = self.env["stock.landed.cost"].create(default_vals)
        stock_landed_cost_1.compute_landed_cost()

        l1 = stock_landed_cost_1.valuation_adjustment_lines
        self.assertAlmostEqual(l1.weight, one_gram_in_kg)
        self.assertEqual(l1.additional_landed_cost, 100)
