/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSale.include({

    _onClickAddQuantity(ev) {
        ev.preventDefault();

        const input = ev.currentTarget
            .closest('.css_quantity')
            .querySelector('input');

        const step = parseInt(
            input.dataset.step || input.getAttribute('step') || 1
        );

        let value = parseInt(input.value || step);
        input.value = value + step;
        input.dispatchEvent(new Event('change'));
    },

    _onClickRemoveQuantity(ev) {
        ev.preventDefault();

        const input = ev.currentTarget
            .closest('.css_quantity')
            .querySelector('input');

        const step = parseInt(
            input.dataset.step || input.getAttribute('step') || 1
        );

        let value = parseInt(input.value || step);
        value = Math.max(step, value - step);

        input.value = value;
        input.dispatchEvent(new Event('change'));
    },

});
