from odoo import models, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty')
    def _check_b2b_qty_multiple(self):
        for line in self:
            # Alleen website orders
            if not line.order_id.website_id:
                continue

            # Alleen B2B website (pas ID aan!)
            if line.order_id.website_id.id != 2:
                continue

            min_qty = line._get_b2b_min_qty()
            if min_qty > 1 and line.product_uom_qty % min_qty != 0:
                raise ValidationError(
                    f"Bestelhoeveelheid moet een veelvoud zijn van {min_qty}"
                )

    def _get_b2b_min_qty(self):
        self.ensure_one()

        pricelist = self.order_id.pricelist_id
        product = self.product_id

        price, rule = product._get_pricelist_price_rule(
            pricelist,
            self.product_uom_qty or 1
        )

        return rule.min_quantity if rule and rule.min_quantity else 1
