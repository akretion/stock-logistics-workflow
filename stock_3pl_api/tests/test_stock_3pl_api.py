from odoo.tests import tagged

from odoo.addons.fastapi.tests.common import FastAPITransactionCase


@tagged("post_install", "-at_install")
class TestStock3PLApi(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup data
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
                "default_code": "TP001",
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        # Create a picking
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": cls.stock_location.id,
                            "location_dest_id": cls.customer_location.id,
                        },
                    )
                ],
            }
        )
        cls.picking.action_confirm()

        # API Key Setup
        cls.api_key_str = "TEST_API_KEY_123"
        cls.env["auth.api.key"].create(
            {
                "name": "Test Key",
                "key": cls.api_key_str,
                "user_id": cls.env.ref("base.user_admin").id,
            }
        )

        cls.endpoint = cls.env.ref("stock_3pl_api.fastapi_endpoint_stock_3pl")

    def test_get_product(self):
        with self._create_test_client(app=self.endpoint._get_app()) as client:
            headers = {"API-KEY": self.api_key_str}
            response = client.get(
                f"{self.endpoint.root_path}/product/{self.product.id}", headers=headers
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["code"], "TP001")

    def test_search_pickings(self):
        with self._create_test_client(app=self.endpoint._get_app()) as client:
            headers = {"API-KEY": self.api_key_str}
            response = client.get(
                f"{self.endpoint.root_path}/picking?id_3pl=false", headers=headers
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            ids = [p["id"] for p in data]
            self.assertIn(self.picking.id, ids)

    def test_process_picking(self):
        self.picking.action_assign()
        with self._create_test_client(app=self.endpoint._get_app()) as client:
            headers = {"API-KEY": self.api_key_str}
            move_id = self.picking.move_ids[0].id

            payload = {
                "moves": [{"id": move_id, "quantity_done": 5.0}],
                "force_reserved_quantities": True,
            }

            url = f"{self.endpoint.root_path}/picking/{self.picking.id}/done"
            response = client.post(url, json=payload, headers=headers)
            self.assertEqual(response.status_code, 200)

            # Fixed: Use invalidate_recordset instead of invalidate_record_cache (V18)
            self.picking.invalidate_recordset()
            self.assertEqual(self.picking.state, "done")

    def test_update_product_qty(self):
        with self._create_test_client(app=self.endpoint._get_app()) as client:
            headers = {"API-KEY": self.api_key_str}
            payload = {"location_id": self.stock_location.id, "new_quantity": 50.0}
            response = client.post(
                f"{self.endpoint.root_path}/product/{self.product.id}",
                json=payload,
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)

            # Fixed: Use invalidate_recordset
            self.product.invalidate_recordset()
            self.assertEqual(
                self.product.with_context(
                    location=self.stock_location.id
                ).qty_available,
                50.0,
            )
