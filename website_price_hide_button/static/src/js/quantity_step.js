/** @odoo-module **/

import publicWidget from "@web/public/public_widget";

publicWidget.registry.QuantityStepCustom = publicWidget.Widget.extend({
    selector: '#wrap', // Gebruik de hoofd-container van de pagina

    init() {
        this._super(...arguments);
        console.log(">>> Widget geïnitialiseerd op de pagina!");
    },
    events: {
        'click .css_quantity .js_add_cart_json': '_onUpdateStepQuantity',
    },

    _onUpdateStepQuantity(ev) {
        console.log(">>> Klik gedetecteerd!");
        const $link = $(ev.currentTarget);
        const $input = $link.closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);

        if (step > 1) {
            ev.preventDefault();
            ev.stopImmediatePropagation(); // DIT IS CRUCIAAL: het stopt de standaard Odoo +1 logica

            const currentValue = parseFloat($input.val() || step);
            const isAdd = $link.find('.fa-plus').length > 0;
            const newValue = isAdd ? currentValue + step : Math.max(step, currentValue - step);

            $input.val(newValue).trigger('change');
            console.log("Nieuwe waarde gezet op:", newValue);
        }
    },
});