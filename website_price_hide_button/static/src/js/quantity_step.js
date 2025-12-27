/** @odoo-module **/

import { publicWidget } from "@web/public/public_widget";

console.log(">>> Custom Quantity Logic geladen");

publicWidget.registry.QuantityStepOverride = publicWidget.Widget.extend({
    selector: '#wrapwrap', // We pakken de hoogste container van de website
    events: {
        'click .js_add_cart_json': '_onQuantityClick',
    },

    _onQuantityClick: function (ev) {
        const $link = $(ev.currentTarget);
        const $input = $link.closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);

        // Alleen onze logica uitvoeren als er een custom step is ingesteld
        if (step > 1) {
            console.log(">>> Custom step gedetecteerd:", step);
            
            // DIT IS DE KEY: we stoppen de originele Odoo-handler van de WebsiteSale widget
            ev.stopImmediatePropagation();
            ev.preventDefault();

            const currentValue = parseFloat($input.val() || 0);
            const isAdd = $link.find('.fa-plus').length > 0;
            
            let newValue = isAdd ? currentValue + step : currentValue - step;
            newValue = Math.max(step, newValue); // Nooit lager dan de stapgrootte

            $input.val(newValue).trigger('change');
        }
    },
});