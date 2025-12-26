/** @odoo-module **/

import { WebsiteSale } from "@website_sale/js/website_sale";
import { patch } from "@web/core/utils/patch";

console.log(">>> Patching WebsiteSale voor custom steps...");

patch(WebsiteSale.prototype, {
    /**
     * @override
     */
    _onClickAddQuantity(ev) {
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);
        
        if (step > 1) {
            const newValue = parseFloat($input.val() || 0) + step;
            $input.val(newValue).trigger('change');
            console.log("Stap aangepast (+):", step);
        } else {
            this._super(...arguments);
        }
    },

    /**
     * @override
     */
    _onClickRemoveQuantity(ev) {
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);
        
        if (step > 1) {
            const currentValue = parseFloat($input.val() || 0);
            const newValue = Math.max(step, currentValue - step);
            $input.val(newValue).trigger('change');
            console.log("Stap aangepast (-):", step);
        } else {
            this._super(...arguments);
        }
    },
});