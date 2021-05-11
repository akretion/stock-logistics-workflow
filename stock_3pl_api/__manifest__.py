# Copyright 2021 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock 3PL Api',
    'summary': """
        Third Party Logistics API for Odoo""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion,Odoo Community Association (OCA)',
    "maintainers": ["rvalyi"],
    'depends': [
        'delivery',
        'base_rest',
        'base_rest_datamodel',
        'auth_api_key',
    ],
    'data': [
    ],
    'demo': [
        "demo/auth_api_key_demo.xml",
    ],
}
