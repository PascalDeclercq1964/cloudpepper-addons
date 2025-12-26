
/** @odoo-module **/
console.log(">>> Quantity Step JS geladen!");
import { publicWidget } from "@web/public/public_widget";

// We gebruiken de klassieke registry voor v18 frontend widgets 
// om conflicten met de nieuwe HTML-editor te voorkomen.
publicWidget.registry.WebsiteSaleQuantityStep = publicWidget.registry.WebsiteSale.extend({
    events: Object.assign({}, publicWidget.registry.WebsiteSale.prototype.events || {}, {
        'click .js_add_cart_json': '_onQuantityClickCustom',
    }),

    _onQuantityClickCustom(ev) {
        ev.preventDefault();
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || $input.data('step') || 1);
        const currentValue = parseFloat($input.val() || step);
        const isAdd = $(ev.currentTarget).has('.fa-plus').length > 0;

        let newValue;
        if (isAdd) {
            newValue = currentValue + step;
        } else {
            newValue = Math.max(step, currentValue - step);
        }

        $input.val(newValue).trigger('change');
    },
});