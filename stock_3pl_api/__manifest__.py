{
    "name": "Stock 3PL Api",
    "summary": "Third Party Logistics API for Odoo (FastAPI)",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "maintainers": ["rvalyi"],
    "depends": [
        "stock",
        "sale_stock",
        "delivery_carrier_info",
        "fastapi",
        "auth_api_key",  # Odoo core or OCA
        "fastapi_auth_api_key",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fastapi_endpoint_data.xml",
    ],
    "demo": [
        "demo/auth_api_key_demo.xml",
    ],
    "external_dependencies": {"python": ["fastapi", "pydantic"]},
    "installable": True,
}
