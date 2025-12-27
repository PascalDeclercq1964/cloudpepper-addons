/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import publicWidget from "@web/legacy/js/public/public_widget";
import "@website_sale/js/website_sale"; // Ensure the original is loaded

patch(publicWidget.registry.WebsiteSale.prototype, {
    /**
     * @override
     */
    _onClickAddCartJSON: function (ev) {
        ev.preventDefault();
        const $link = $(ev.currentTarget);
        const $input = $link.closest('.input-group').find("input");
        const customStep = 5; // Define your custom step here

        let quantity = parseFloat($input.val() || 0);
        if ($link.has(".fa-minus").length) {
            quantity -= customStep;
        } else {
            quantity += customStep;
        }
        
        // Apply constraints (min/max)
        const min = parseFloat($input.data("min") || 1);
        const max = parseFloat($input.data("max") || Infinity);
        const finalQty = Math.max(min, Math.min(max, quantity));

        $input.val(finalQty).trigger('change');
    },
});
