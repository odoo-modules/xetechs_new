
from openerp import api, models

class ComboSaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        res = super(ComboSaleOrder, self).action_confirm()
        pickings_id = self.picking_ids
        picking_lines = []
        for line in self.order_line:
            if line.product_id.combo_product_id:
                for pack_id in line.product_id.combo_product_id:
                    qty = pack_id.product_quantity * line.product_uom_qty
                    picking_lines.append((0, 0, {
                        'name': pack_id.product_id.name,
                        'product_id': pack_id.product_id.id,
                        'product_uom_qty': qty,
                        'picking_id': pickings_id.id,
                        'product_uom': pack_id.uom_id.id,
                        'location_id': pickings_id.move_lines[0].location_id.id,
                        'location_dest_id': pickings_id.move_lines[0].location_dest_id.id,
                        'state': 'draft'}))
        pickings_id.move_lines = picking_lines
        pickings_id.action_assign()
        for move in pickings_id.move_lines:
            move._action_assign()
            move.filtered(lambda m: m.product_id.tracking == 'none')._action_done()
        return res
