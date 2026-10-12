# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestProductQuantitiesByRestrictedLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product with restricted-lot forecasts",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "Named lot",
                "product_id": cls.product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.env["stock.quant"].create(
            [
                {
                    "product_id": cls.product.id,
                    "location_id": cls.stock_location.id,
                    "quantity": 11,
                },
                {
                    "product_id": cls.product.id,
                    "location_id": cls.stock_location.id,
                    "lot_id": cls.lot.id,
                    "quantity": 17,
                },
            ]
        )
        cls._create_pending_move(cls.supplier_location, cls.stock_location, 3)
        cls._create_pending_move(
            cls.supplier_location, cls.stock_location, 5, lot=cls.lot
        )
        cls._create_pending_move(cls.stock_location, cls.customer_location, 7)
        cls._create_pending_move(
            cls.stock_location, cls.customer_location, 13, lot=cls.lot
        )

    @classmethod
    def _create_pending_move(cls, source, destination, quantity, lot=False):
        move = cls.env["stock.move"].create(
            {
                "name": "Restricted-lot forecast move",
                "product_id": cls.product.id,
                "product_uom_qty": quantity,
                "product_uom": cls.product.uom_id.id,
                "location_id": source.id,
                "location_dest_id": destination.id,
                "restrict_lot_id": lot.id if lot else False,
            }
        )
        move._action_confirm()

    def _assert_quantities(self, context, expected):
        product = self.product.with_context(
            location=self.stock_location.id,
            **context,
        )
        self.assertRecordValues(product, [expected])

    def test_quantities_without_lot_context_include_all_lots(self):
        expected = {
            "qty_available": 28.0,
            "incoming_qty": 8.0,
            "outgoing_qty": 20.0,
            "virtual_available": 16.0,
        }
        self._assert_quantities({}, expected)
        self._assert_quantities({"lot_id": None}, expected)

    def test_quantities_with_false_lot_context_only_include_no_lot(self):
        self._assert_quantities(
            {"lot_id": False},
            {
                "qty_available": 11.0,
                "incoming_qty": 3.0,
                "outgoing_qty": 7.0,
                "virtual_available": 7.0,
            },
        )

    def test_quantities_with_named_lot_context_only_include_that_lot(self):
        self._assert_quantities(
            {"lot_id": self.lot.id},
            {
                "qty_available": 17.0,
                "incoming_qty": 5.0,
                "outgoing_qty": 13.0,
                "virtual_available": 9.0,
            },
        )
