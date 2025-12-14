odoo.define('website_hide_button.product_page', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var TARGET_WEBSITE_ID = 2;
    
    publicWidget.registry.WebsiteHideButton = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {},
        
        /**
         * @override
         */
        start: function () {
            var self = this;
            console.log("Website ID:", odoo.session_info.website_id);
            return this._super.apply(this, arguments).then(function () {
                if (odoo.session_info && odoo.session_info.is_public_user && odoo.session_info.website_id === TARGET_WEBSITE_ID) {
                    self._hideProductPrices();
                    self._hideAddToCartButtons();
                    self._hideQuantitySelectors();
                    self._hidePriceFilters();
                    self._addContactUsButtons();
                }
            });
        },
        
        _hideProductPrices: function () {
            $('.product_price, .oe_price, .oe_currency_value').hide();
            
            $('.o_wsale_product_grid_wrapper .product_price').hide();
            $('.o_wsale_products_item_price').hide();
            
            $('.oe_website_sale span[data-oe-type="monetary"]').hide();
            $('.o_wsale_products_item_price span').hide();
            
            $('[t-field="product.list_price"]').hide();
            $('[t-field="product.price"]').hide();
            $('.oe_currency_value').hide();
            
            $('.oe_website_sale .oe_product_prices').hide();
        },
        
        /**
         * Hide add to cart buttons
         */
        _hideAddToCartButtons: function () {
            $('#add_to_cart_wrap, .o_add_wishlist_dyn').hide();
            
            $('.o_wsale_product_btn form, .o_wsale_product_btn button[type="submit"], .o_wsale_product_btn .o_add_wishlist_dyn').hide();
            
            $('header .o_wsale_my_cart').hide();
        },
        
        /**
         * Add contact us buttons
         */
        _addContactUsButtons: function () {
            if ($('#add_to_cart_wrap').length && !$('#contact_us_button').length) {
                $('#add_to_cart_wrap').before(
                    '<div id="contact_us_button" class="mt-2 mb-3">' +
                    '    <div class="alert alert-info mt-3">' +
                    '        <i class="fa fa-info-circle me-2"></i>' +
                    '        <span>Please log in to see prices and purchase options.</span>' +
                    '    </div>' +
                    '    <a href="/contactus" class="btn btn-primary btn-md">' +
                    '        <i class="fa fa-envelope me-2"></i>' +
                    '        <span>Contact Us</span>' +
                    '    </a>' 
                    +
                    '</div>'
                );
            }
            
            $('.o_wsale_product_grid_wrapper .o_wsale_product_btn').each(function() {
                if (!$(this).find('.contact_us_grid_btn').length && !$(this).find('a[href="/contactus"]').length) {
                    $(this).append(
                        '<div class="contact_us_grid_btn mt-2">' +
                        '    <a href="/contactus" class="btn btn-primary btn-sm w-100">' +
                        '        <i class="fa fa-envelope me-1"></i>' +
                        '        <span>Contact Us</span>' +
                        '    </a>' +
                        '</div>'
                    );
                }
            });
        },
        
        /**
         * Hide quantity selectors
         */
        _hideQuantitySelectors: function () {
            $('.css_quantity').hide();
        },
        
        /**
         * Hide price filters in shop
         */
        _hidePriceFilters: function () {
            $('#o_wsale_price_range_option').hide();
        }
    });
    
    return publicWidget.registry.WebsiteHideButton;

});

