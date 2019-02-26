# Copyright 2019 Akretion (http://www.akretion.com)
# Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Stock Picking Exceptions',
    'summary': 'Custom exceptions on stock.picking',
    'version': '12.0.1.0.0',
    'category': 'Stock',
    'author': "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    'depends': [
        'stock',
        'base_exception',
    ],
    'license': 'AGPL-3',
    'data': [
        # 'data/picking_exception_data.xml',
        # 'wizard/picking_exception_confirm_view.xml',
        'views/stock_view.xml',
    ],
    'installable': True,
}
