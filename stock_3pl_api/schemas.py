from datetime import date

from pydantic import BaseModel, ConfigDict, Field

# --- Helper Models ---


class PartnerInfo(BaseModel):
    id: int
    name: str
    email: str | None = ""
    street: str | None = ""
    street2: str | None = ""
    zip_code: str | None = Field(alias="zip", default="")
    city: str | None = ""
    phone: str | None = ""
    mobile: str | None = ""
    state_name: str | None = None
    country_code: str | None = None
    is_company: bool = False

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProductShortInfo(BaseModel):
    id: int
    name: str
    # Fixed: Removed alias="default_code" to ensure JSON key is 'code'
    # We will map product.default_code -> code explicitly in the router
    code: str | None = ""
    barcode: str | None = ""
    weight: float | None = 0.0
    volume: float | None = 0.0

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProductInfo(ProductShortInfo):
    description: str | None = ""
    category_name: str
    uom_name: str
    tracking_type: str
    quantity: float
    available_quantity: float
    incoming_quantity: float
    outgoing_quantity: float

    # For mapping from Odoo record
    model_config = ConfigDict(from_attributes=True)


class PackageUpdateParam(BaseModel):
    ref: str
    weight: float | None = None
    tracking_url: str | None = None


class MoveLineInfo(BaseModel):
    id: int
    quantity: float
    reserved_quantity: float | None = 0.0
    lot: str | None = ""
    package_ref: str | None = None
    package_tracking_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MoveInfo(BaseModel):
    id: int
    product: ProductShortInfo
    quantity: float
    quantity_uom: float
    uom_name: str
    origin: str
    dest: str
    state: str
    id_3pl: str | None = ""
    lines: list[MoveLineInfo] = []

    model_config = ConfigDict(from_attributes=True)


class PickingInfo(BaseModel):
    id: int
    name: str
    origin: str | None = ""
    partner: PartnerInfo | None = None
    picking_type_name: str | None = ""
    state: str
    scheduled_date: date
    id_3pl: str | None = ""
    moves: list[MoveInfo] = []
    backorder_id: int | None = None
    backorder_ids: list[int] = []
    carrier_code: str | None = None
    pickup_code: str | None = None
    customer_order_ref: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Parameters for endpoints ---


class MoveLineUpdateParam(BaseModel):
    quantity: float
    lot_id: str | None = None
    package: PackageUpdateParam | None = None


class MoveUpdateParam(BaseModel):
    id: int
    scheduled_date: date | None = None
    date_done: date | None = None
    id_3pl: str | None = None
    quantity_done: float | None = None
    lines: list[MoveLineUpdateParam] = []
    exception: str | None = None


class PickingUpdateParam(BaseModel):
    scheduled_date: date | None = None
    date_done: date | None = None
    exception: str | None = None
    id_3pl: str | None = None
    moves: list[MoveUpdateParam] = []


class PickingDoneParam(PickingUpdateParam):
    cancel_backorder: bool = False
    force_reserved_quantities: bool = False


class ProductUpdateParam(BaseModel):
    location_name: str | None = None
    location_id: int | None = None
    new_quantity: float | None = None
    delta_quantity: float | None = None
