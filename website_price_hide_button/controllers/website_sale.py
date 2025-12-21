from odoo import models, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty')
    def _check_b2b_qty_multiple(self):
        for line in self:
            if not line.order_id.website_id:
                continue

            # enkel B2B website
            if line.order_id.website_id.id != 2:
                continue

            min_qty = line._get_b2b_min_qty()
            if min_qty > 1 and line.product_uom_qty % min_qty != 0:
                raise ValidationError(
                    f"Bestelhoeveelheid moet een veelvoud zijn van {min_qty}"
                )
