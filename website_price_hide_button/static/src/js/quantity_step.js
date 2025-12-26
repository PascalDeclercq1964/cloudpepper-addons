/** @odoo-module **/

import { WebsiteSale } from "@website_sale/js/website_sale";
import { patch } from "@web/core/utils/patch";

patch(WebsiteSale.prototype, {
    /**
     * Overschrijf de plus-knop logica
     */
    _onClickAddQuantity(ev) {
        ev.preventDefault();
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseInt($input.attr('step') || $input.data('step') || 1);
        const currentValue = parseInt($input.val() || step);
        
        $input.val(currentValue + step).trigger('change');
    },

    /**
     * Overschrijf de min-knop logica
     */
    _onClickRemoveQuantity(ev) {
        ev.preventDefault();
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseInt($input.attr('step') || $input.data('step') || 1);
        const currentValue = parseInt($input.val() || step);
        
        const newValue = Math.max(step, currentValue - step);
        $input.val(newValue).trigger('change');
    },
});