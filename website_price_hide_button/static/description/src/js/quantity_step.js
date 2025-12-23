odoo.define('my_module.quantity_step', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.WebsiteSale.include({

        _onClickAddQuantity(ev) {
            ev.preventDefault();
            const $input = $(ev.currentTarget)
                .closest('.css_quantity')
                .find('input');

            const step = parseInt($input.data('step') || $input.attr('step') || 1);
            let value = parseInt($input.val(), 10) || 0;

            $input.val(value + step).change();
        },

        _onClickRemoveQuantity(ev) {
            ev.preventDefault();
            const $input = $(ev.currentTarget)
                .closest('.css_quantity')
                .find('input');

            const step = parseInt($input.data('step') || $input.attr('step') || 1);
            let value = parseInt($input.val(), 10) || 0;

            value = Math.max(step, value - step);
            $input.val(value).change();
        },

    });
});
