from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from odoo import _
from odoo.api import Environment
from odoo.models import expression

from ..dependencies import auth_env
from ..schemas import (
    PickingDoneParam,
    PickingInfo,
    PickingUpdateParam,
    ProductInfo,
    ProductUpdateParam,
)

router = APIRouter(prefix="", tags=["stock_3pl"])

# --- HELPERS TO MAP ODOO OBJECTS TO PYDANTIC ---


def _to_picking_info(picking):
    moves_data = []
    for move in picking.move_ids_without_package:
        lines_data = []
        for line in move.move_line_ids:
            lines_data.append(
                {
                    "id": line.id,
                    "quantity": line.quantity,
                    "reserved_quantity": line.quantity_product_uom,
                    "lot": line.lot_id.name if line.lot_id else "",
                    "package_ref": line.result_package_id.name
                    if line.result_package_id
                    else None,
                    "package_tracking_url": line.result_package_id.tracking_url
                    if line.result_package_id and line.result_package_id.tracking_url
                    else None,
                }
            )

        moves_data.append(
            {
                "id": move.id,
                "product": {
                    "id": move.product_id.id,
                    "name": move.product_id.name,
                    "code": move.product_id.default_code or "",
                    "barcode": move.product_id.barcode or "",
                    "weight": move.product_id.weight or 0.0,
                    "volume": move.product_id.volume or 0.0,
                },
                "quantity": move.product_qty,
                "quantity_uom": move.product_uom_qty,
                "uom_name": move.product_uom.name,
                "origin": move.location_id.name,
                "dest": move.location_dest_id.name,
                "state": move.state,
                "id_3pl": "",
                "lines": lines_data,
            }
        )

    partner_data = None
    if picking.partner_id:
        p = picking.partner_id
        partner_data = {
            "id": p.id,
            "name": p.name,
            "email": p.email or "",
            "street": p.street or "",
            "street2": p.street2 or "",
            "zip": p.zip or "",
            "city": p.city or "",
            "phone": p.phone or "",
            "mobile": p.mobile or "",
            "state_name": p.state_id.name if p.state_id else None,
            "country_code": p.country_id.code if p.country_id else None,
            "is_company": p.is_company,
        }

    carrier_code = None
    carrier = getattr(picking, "carrier_id", None)
    if carrier:
        carrier_code = getattr(carrier, "code", None) or carrier.name

    sale_id = getattr(picking, "sale_id", None)

    # Fix: Ensure False from Odoo is converted to None for optional string fields
    pickup_code = getattr(sale_id, "x_carrier_pickup", None) if sale_id else None
    if not pickup_code:
        pickup_code = None

    customer_order_ref = getattr(sale_id, "client_order_ref", None) if sale_id else None
    if not customer_order_ref:
        customer_order_ref = None

    return PickingInfo(
        id=picking.id,
        name=picking.name,
        origin=picking.origin or "",
        partner=partner_data,
        picking_type_name=picking.picking_type_id.name,
        state=picking.state,
        scheduled_date=picking.scheduled_date.date()
        if picking.scheduled_date
        else date.today(),
        id_3pl=picking.id_3pl
        or "",  # id_3pl is optional string in schema but defaulted to "" if None? No, schema says Optional[str] = ""
        moves=moves_data,
        backorder_id=picking.backorder_id.id if picking.backorder_id else None,
        backorder_ids=picking.backorder_ids.ids,
        carrier_code=carrier_code,
        pickup_code=pickup_code,
        customer_order_ref=customer_order_ref,
    )


def _to_product_info(product, ctx_env):
    return ProductInfo(
        id=product.id,
        name=product.name,
        code=product.default_code or "",
        description=product.description or "",
        barcode=product.barcode or "",
        weight=product.weight or 0.0,
        volume=product.volume or 0.0,
        category_name=product.categ_id.name,
        uom_name=product.uom_id.name,
        tracking_type=product.tracking,
        quantity=product.qty_available,
        available_quantity=product.virtual_available,
        incoming_quantity=product.incoming_qty,
        outgoing_quantity=product.outgoing_qty,
    )


# --- ROUTES ---


@router.get("/picking", response_model=list[PickingInfo])
def search_pickings(
    env: Annotated[Environment, Depends(auth_env)],
    picking_type_name: str | None = None,
    picking_type_id: int | None = None,
    states: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    origin: str | None = None,
    id_3pl: str | None = None,
):
    domain = []
    if picking_type_id:
        domain = expression.AND([domain, [("picking_type_id", "=", picking_type_id)]])
    elif picking_type_name:
        domain = expression.AND(
            [domain, [("picking_type_id.name", "ilike", picking_type_name)]]
        )

    if origin:
        domain = expression.AND([domain, [("origin", "ilike", origin)]])

    if states:
        if "|" in states:
            s_list = states.split("|")
        else:
            s_list = [states]
        domain = expression.AND([domain, [("state", "in", s_list)]])

    if date_from:
        domain = expression.AND([domain, [("scheduled_date", ">", date_from)]])
    if date_to:
        domain = expression.AND([domain, [("scheduled_date", "<", date_to)]])

    if id_3pl:
        if id_3pl.lower() == "false":
            domain = expression.AND([domain, [("id_3pl", "=", False)]])
        elif id_3pl == "*":
            domain = expression.AND([domain, [("id_3pl", "!=", False)]])
        else:
            domain = expression.AND([domain, [("id_3pl", "=", id_3pl)]])

    pickings = env["stock.picking"].search(domain)
    return [_to_picking_info(p) for p in pickings]


@router.get("/picking/{id}", response_model=PickingInfo)
def get_picking(id: int, env: Annotated[Environment, Depends(auth_env)]):
    picking = env["stock.picking"].browse(id)
    if not picking.exists():
        raise HTTPException(404, "Picking not found")
    return _to_picking_info(picking)


@router.post("/picking/{id}", response_model=PickingInfo)
def update_picking(
    id: int, params: PickingUpdateParam, env: Annotated[Environment, Depends(auth_env)]
):
    picking = env["stock.picking"].browse(id)
    if not picking.exists():
        raise HTTPException(404, "Picking not found")

    if params.moves:
        allowed_move_ids = picking.move_ids_without_package.ids
        for move_data in params.moves:
            if move_data.id not in allowed_move_ids:
                raise HTTPException(
                    400, f"Move {move_data.id} doesn't belong to picking {id}"
                )

            move = env["stock.move"].browse(move_data.id)
            move.move_line_ids.unlink()

            if move_data.lines:
                for line_data in move_data.lines:
                    package_id = False
                    if line_data.package:
                        package = env["stock.quant.package"].search(
                            [("name", "=", line_data.package.ref)], limit=1
                        )
                        if package:
                            package.write(
                                {
                                    "shipping_weight": line_data.package.weight,
                                    "tracking_url": line_data.package.tracking_url,
                                }
                            )
                        else:
                            package = env["stock.quant.package"].create(
                                {
                                    "name": line_data.package.ref,
                                    "shipping_weight": line_data.package.weight,
                                    "tracking_url": line_data.package.tracking_url,
                                }
                            )
                        package_id = package.id

                    env["stock.move.line"].create(
                        {
                            "move_id": move.id,
                            "picking_id": picking.id,
                            "product_id": move.product_id.id,
                            "quantity": line_data.quantity,
                            "product_uom_id": move.product_uom.id,
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                            "result_package_id": package_id,
                        }
                    )
            elif move_data.quantity_done is not None:
                env["stock.move.line"].create(
                    {
                        "move_id": move.id,
                        "picking_id": picking.id,
                        "product_id": move.product_id.id,
                        "quantity": move_data.quantity_done,
                        "product_uom_id": move.product_uom.id,
                        "location_id": move.location_id.id,
                        "location_dest_id": move.location_dest_id.id,
                    }
                )

    vals = {}
    if params.scheduled_date:
        vals["scheduled_date"] = params.scheduled_date
    if params.date_done:
        vals["date_done"] = params.date_done
    if params.id_3pl:
        vals["id_3pl"] = params.id_3pl

    if vals:
        picking.write(vals)

    return _to_picking_info(picking)


@router.post("/picking/{id}/done", response_model=PickingInfo)
def done_picking(
    id: int, params: PickingDoneParam, env: Annotated[Environment, Depends(auth_env)]
):
    update_params = PickingUpdateParam(**params.model_dump())
    picking_info = update_picking(id, update_params, env)

    picking = env["stock.picking"].browse(id)

    if picking.state == "draft":
        picking.action_confirm()

    if picking.state != "assigned":
        picking.action_assign()

    if params.force_reserved_quantities:
        for move in picking.move_ids.filtered(
            lambda m: m.state not in ["done", "cancel"]
        ):
            for line in move.move_line_ids:
                line.quantity = line.quantity_product_uom

    picking.button_validate()

    if params.cancel_backorder:
        backorders = env["stock.picking"].search([("backorder_id", "=", picking.id)])
        if backorders:
            backorders.action_cancel()
            picking.message_post(body=_("Backorder cancelled by 3PL API"))

    return _to_picking_info(picking)


# --- PRODUCT ROUTES ---


@router.get("/product", response_model=list[ProductInfo])
def search_products(
    env: Annotated[Environment, Depends(auth_env)],
    location_name: str | None = None,
    location_id: int | None = None,
):
    ctx = {}
    if location_id:
        ctx["location"] = location_id
    elif location_name:
        loc = env["stock.location"].search([("name", "ilike", location_name)], limit=1)
        if loc:
            ctx["location"] = loc.id

    products = (
        env["product.product"].with_context(**ctx).search([("type", "=", "consu")])
    )
    return [_to_product_info(p, env) for p in products]


@router.get("/product/{id}", response_model=ProductInfo)
def get_product(
    id: int,
    env: Annotated[Environment, Depends(auth_env)],
    location_name: str | None = None,
    location_id: int | None = None,
):
    ctx = {}
    if location_id:
        ctx["location"] = location_id
    elif location_name:
        loc = env["stock.location"].search([("name", "ilike", location_name)], limit=1)
        if loc:
            ctx["location"] = loc.id

    product = env["product.product"].with_context(**ctx).browse(id)
    if not product.exists():
        raise HTTPException(404, "Product not found")
    return _to_product_info(product, env)


@router.post("/product/{id}", response_model=ProductInfo)
def update_product_qty(
    id: int, params: ProductUpdateParam, env: Annotated[Environment, Depends(auth_env)]
):
    loc_id = None
    if params.location_id:
        loc_id = params.location_id
    elif params.location_name:
        loc = env["stock.location"].search(
            [("name", "ilike", params.location_name)], limit=1
        )
        if loc:
            loc_id = loc.id

    if not loc_id:
        raise HTTPException(400, "location_id or location_name required")

    product = env["product.product"].browse(id)
    if not product.exists():
        raise HTTPException(404, "Product not found")

    if params.new_quantity is not None:
        current_qty = product.with_context(location=loc_id).qty_available
        delta = params.new_quantity - current_qty
        if delta != 0:
            env["stock.quant"]._update_available_quantity(
                product, env["stock.location"].browse(loc_id), delta
            )
    elif params.delta_quantity is not None:
        env["stock.quant"]._update_available_quantity(
            product, env["stock.location"].browse(loc_id), params.delta_quantity
        )
    else:
        raise HTTPException(400, "new_quantity or delta_quantity required")

    env.flush_all()

    return _to_product_info(product.with_context(location=loc_id), env)
