from odoo import models, fields, tools

class MarketplaceProductFeed(models.Model):
    _name = "x_marketplace.product.feed"
    _description = "Marketplace Product Feed"
    _auto = False
    _rec_name = "sku"

    product_template_id = fields.Many2one("product.template", readonly=True)
    sku = fields.Char(readonly=True)
    barcode = fields.Char(readonly=True)
    price = fields.Float(readonly=True)
    qty_available = fields.Float(readonly=True)
    category_name = fields.Char(readonly=True)

    name_nl = fields.Char(readonly=True)
    name_fr = fields.Char(readonly=True)
    name_de = fields.Char(readonly=True)
    name_en = fields.Char(readonly=True)

    description_nl = fields.Html(readonly=True)
    description_fr = fields.Html(readonly=True)
    description_de = fields.Html(readonly=True)
    description_en = fields.Html(readonly=True)

    product_url = fields.Char(readonly=True)

    image_1 = fields.Char(readonly=True)
    image_2 = fields.Char(readonly=True)
    image_3 = fields.Char(readonly=True)
    image_4 = fields.Char(readonly=True)
    image_5 = fields.Char(readonly=True)


