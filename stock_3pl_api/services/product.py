from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class ProductService(Component):
    """
    Product API
    examples:
    curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/product
    curl -H "api_key: key1"  http://localhost:8069/stock_3pl_api/product/13
    """
    _inherit = 'base.stock.3pl.api.service'
    _name = 'base.stock.3pl.api.product'
    _usage = 'product'
    _collection = 'stock.3pl.api.service'
    _description = "Export the product catalog with stock levels"

    @restapi.method(
        [(["/"], "GET")],
        input_param=Datamodel("product.search.param"),
        output_param=Datamodel("product.info", is_list=True),
        auth="api_key",
    )
    def search(self, product_search_param):
        """
        List products and their inventory data
        """
        res = []
        # TODO use location_name for context
        # see stock/models/stock_rule.py#L491
        if product_search_param.location_id:
            ctx = {'location': product_search_param.location_id}
        elif product_search_param.location_name:
            ctx = {'location': product_search_param.location_name}
        else:
            ctx = {}
        for p in self.env["product.product"].with_context(ctx).search(
            [('type', 'in', ['consu', 'product'])]
        ):
            res.append(self._to_product_info(p))
        return res

    @restapi.method(
        [(["/<int:id>", "/<int:id>"], "GET")],
        input_param=Datamodel("product.search.param"),
        output_param=Datamodel("product.info"),
        auth="api_key",
    )
    def get(self, _id, product_search_param):
        """
        Get product information
        """
        if product_search_param.location_id:
            ctx = {'location': product_search_param.location_id}
        elif product_search_param.location_name:
            ctx = {'location': product_search_param.location_name}
        else:
            ctx = {}
        product = self.env["product.product"].with_context(ctx).browse(_id)
        return self._to_product_info(product)

    def _to_product_info(self, product):
        # TODO export related product.packaging too?
        ProductInfo = self.env.datamodels["product.info"]
        product_info = ProductInfo(partial=True)
        product_info.id = product.id

        product_info.name = product.name
        product_info.code = product.default_code
        product_info.description = product.description
        product_info.barcode = product.barcode
        product_info.weight = product.weight
        product_info.volume = product.volume
        product_info.category_name = product.categ_id.name
        product_info.uom_name = product.uom_id.name
        product_info.tracking_type = product.tracking

        product_info.quantity = product.qty_available
        product_info.incoming_quantity = product.incoming_qty
        product_info.outgoing_quantity = product.outgoing_qty
        return product_info
