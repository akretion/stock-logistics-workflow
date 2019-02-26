# Copyright 2019 Akretion (http://www.akretion.com)
# Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = ['stock.picking', 'base.exception']
    _name = 'stock.picking'
    _picking = 'main_exception_id asc, scheduled_date desc, name desc'

    rule_group = fields.Selection(
        selection_add=[('picking', 'Picking')],
        default='picking',
    )

    @api.model
    def test_all_draft_pickings(self):
        picking = self.search([('state', '=', 'draft')])
        picking.test_exceptions()
        return True

    @api.constrains('ignore_exception', 'move_ids_without_package', 'state')
    def picking_check_exception(self):
        pickings = self.filtered(lambda s: s.state == 'assigned')
        if pickings:
            pickings._check_exception()

    @api.onchange('move_ids_without_package')
    def onchange_ignore_exception(self):
        if self.state == 'picking':
            self.ignore_exception = False

    @api.multi
    def action_confirm(self):
        if self.detect_exceptions() and not self.ignore_exception:
            return self._popup_exceptions()
        return super(StockPicking, self).action_confirm()

    def toto(self):
        print(self)
        import pdb; pdb.set_trace()

    def _picking_get_lines(self):
        self.ensure_one()
        return self.move_ids_without_package

    @api.model
    def _get_popup_action(self):
        action = self.env.ref(
            'picking_exception.action_picking_exception_confirm')
        return action
