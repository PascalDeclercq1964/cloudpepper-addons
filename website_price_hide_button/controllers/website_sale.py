# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleInherit(WebsiteSale):
    """Class to hide price and replace buy button with contact us"""

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Add login_user to context"""
        res = super().shop(page, category, search, min_price,
                           max_price, ppg, **post)
        res.qcontext.update({
            'login_user': request.env.user._is_public()
        })
        return res

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Add login_user to product page context"""
        res = super(WebsiteSaleInherit, self)._prepare_product_values(product,
                                                                      category,
                                                                      search,
                                                                      **kwargs)
        res['login_user'] = request.env.user._is_public()
        return res

    @http.route()
    def shop_payment(self, **post):
        """Restrict public visitors from accessing payment page"""
        user = http.request.env.user
        if not user._is_public() and (user.has_group('base.group_portal') or 
                                     user.has_group('base.group_user')):
            res = super(WebsiteSaleInherit, self).shop_payment(**post)
            return res
        return request.redirect("/")
