from odoo import models, fields, tools
import logging

_logger = logging.getLogger(__name__)

# DIT GAAT ONS VERTELLEN OF HET BESTAND GELADEN WORDT
_logger.info(">>>> HET BESTAND MARKETPLACE_PRODUCT_FEED WORDT GELADEN <<<<")


class MarketplaceProductFeed(models.Model):
    _name = "x_marketplace.product.feed"
    _description = "TEST FEED 123"
    _auto = False
    _table = 'marketplace_product_feed'
    _rec_name = "sku"

    # Velden definities
    id = fields.Integer(readonly=True)
    product_product_id = fields.Many2one("product.product", readonly=True)
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
    
    # De nieuwe velden
    age_from = fields.Integer(readonly=True)
    age_to = fields.Integer(readonly=True)
    ce_document = fields.Char(readonly=True)
    bol_category = fields.Char(readonly=True)
    kaufland_category = fields.Char(readonly=True)

def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # We gebruiken een subquery om de GROUP BY makkelijker te maken
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH ordered_images AS (
                    SELECT
                        pi.product_tmpl_id,
                        'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920' AS url,
                        ROW_NUMBER() OVER (PARTITION BY pi.product_tmpl_id ORDER BY pi.sequence, pi.id) AS rn
                    FROM product_image pi
                ),
                stock_data AS (
                    SELECT 
                        product_id, 
                        SUM(quantity - reserved_quantity) as available 
                    FROM stock_quant 
                    GROUP BY product_id
                )
                SELECT
                    pt.id AS id,
                    pp.id AS product_product_id,
                    pt.default_code AS sku,
                    pp.barcode AS barcode,
                    pt.list_price AS price,
                    COALESCE(sd.available, 0) AS qty_available,
                    pc.complete_name AS category_name,
                    pt.name ->> 'nl_BE' AS name_nl,
                    pt.name ->> 'fr_FR' AS name_fr,
                    pt.name ->> 'de_DE' AS name_de,
                    pt.name ->> 'en_US' AS name_en,
                    pt.description_ecommerce ->> 'nl_BE' AS description_nl,
                    pt.description_ecommerce ->> 'fr_FR' AS description_fr,
                    pt.description_ecommerce ->> 'de_DE' AS description_de,
                    pt.description_ecommerce ->> 'en_US' AS description_en,
                    '/shop/product/' || pt.id AS product_url,
                    (SELECT url FROM ordered_images WHERE product_tmpl_id = pt.id AND rn = 1 LIMIT 1) AS image_1,
                    (SELECT url FROM ordered_images WHERE product_tmpl_id = pt.id AND rn = 2 LIMIT 1) AS image_2,
                    (SELECT url FROM ordered_images WHERE product_tmpl_id = pt.id AND rn = 3 LIMIT 1) AS image_3,
                    (SELECT url FROM ordered_images WHERE product_tmpl_id = pt.id AND rn = 4 LIMIT 1) AS image_4,
                    (SELECT url FROM ordered_images WHERE product_tmpl_id = pt.id AND rn = 5 LIMIT 1) AS image_5,
                    pt.x_studio_leeftijd_van AS age_from,
                    pt.x_studio_leeftijd_tot AS age_to,
                    pt.x_studio_ce_document AS ce_document,
                    pt.x_studio_bol_category AS bol_category,
                    pt.x_studio_kaufland_category AS kaufland_category
                FROM product_template pt
                JOIN product_product pp ON pp.product_tmpl_id = pt.id
                LEFT JOIN stock_data sd ON sd.product_id = pp.id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                WHERE pt.active = TRUE
            )
        """ % self._table)