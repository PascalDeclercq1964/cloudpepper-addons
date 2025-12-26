/** @odoo-module **/

import { WebsiteSale } from "@website_sale/js/website_sale";
import { patch } from "@web/core/utils/patch";

// We checken of WebsiteSale wel bestaat voordat we patchen
if (WebsiteSale) {
    patch(WebsiteSale.prototype, {
        _onClickAddQuantity(ev) {
            ev.preventDefault();
            const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
            const step = parseFloat($input.attr('step') || $input.data('step') || 1);
            const currentValue = parseFloat($input.val() || step);
            
            $input.val(currentValue + step).trigger('change');
        },

        _onClickRemoveQuantity(ev) {
            ev.preventDefault();
            const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
            const step = parseFloat($input.attr('step') || $input.data('step') || 1);
            const currentValue = parseFloat($input.val() || step);
            
            const newValue = Math.max(step, currentValue - step);
            $input.val(newValue).trigger('change');
        },
    });
}