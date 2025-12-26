/** @odoo-module **/

import { publicWidget } from "@web/public/public_widget";

// We breiden de bestaande WebsiteSale uit in plaats van een nieuwe te maken
publicWidget.registry.WebsiteSale.include({
    
    _onClickAddQuantity(ev) {
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);
        
        if (step > 1) {
            ev.preventDefault();
            // We berekenen het handmatig
            const newValue = parseFloat($input.val()) + step;
            $input.val(newValue).trigger('change');
            console.log("Custom stap toegevoegd:", step);
        } else {
            this._super(...arguments); // Gebruik standaard Odoo gedrag (1)
        }
    },

    _onClickRemoveQuantity(ev) {
        const $input = $(ev.currentTarget).closest('.css_quantity').find('input');
        const step = parseFloat($input.attr('step') || 1);
        
        if (step > 1) {
            ev.preventDefault();
            const newValue = Math.max(step, parseFloat($input.val()) - step);
            $input.val(newValue).trigger('change');
            console.log("Custom stap verwijderd:", step);
        } else {
            this._super(...arguments);
        }
    },
});