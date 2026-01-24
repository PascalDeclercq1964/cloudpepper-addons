from odoo import models, fields, tools
import logging

_logger = logging.getLogger(__name__)

# DIT GAAT ONS VERTELLEN OF HET BESTAND GELADEN WORDT
_logger.info(">>>> HET BESTAND MARKETPLACE_PRODUCT_FEED WORDT GELADEN <<<<")


class MarketplaceProductFeed(models.Model):
    _name = "x_marketplace.product.feed"
    _description = "Marketplace Product Feed"
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
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH ordered_images AS (
                    SELECT
                        pi.product_tmpl_id,
                        'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920' AS url,
                        ROW_NUMBER() OVER (PARTITION BY pi.product_tmpl_id ORDER BY pi.sequence, pi.id) AS rn
                    FROM product_image pi
                )
                SELECT
                    pt.id AS id,
                    pp.id AS product_product_id,
                    pt.default_code AS sku,
                    pp.barcode AS barcode,
                    pt.list_price AS price,
                    COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS qty_available,
                    pc.complete_name AS category_name,
                    pt.name ->> 'nl_BE' AS name_nl,
                    pt.name ->> 'fr_FR' AS name_fr,
                    pt.name ->> 'de_DE' AS name_de,
                    pt.name ->> 'en_US' AS name_en,
                    pt.description_ecommerce ->> 'nl_BE' AS description_nl,
                    pt.description_ecommerce ->> 'fr_FR' AS description_fr,
                    pt.description_ecommerce ->> 'de_DE' AS description_de,
                    pt.description_ecommerce ->> 'en_US' AS description_en,
                    'https://www.chameleonstars.com/shop/product/' || pt.id AS product_url,
                    
                    -- Afbeeldingen (MAX/CASE constructie)
                    MAX(CASE WHEN oi.rn = 1 THEN oi.url END) AS image_1,
                    MAX(CASE WHEN oi.rn = 2 THEN oi.url END) AS image_2,
                    MAX(CASE WHEN oi.rn = 3 THEN oi.url END) AS image_3,
                    MAX(CASE WHEN oi.rn = 4 THEN oi.url END) AS image_4,
                    MAX(CASE WHEN oi.rn = 5 THEN oi.url END) AS image_5,
                    
                    pt.x_studio_leeftijd_van AS age_from,
                    pt.x_studio_leeftijd_tot AS age_to,

                    -- CE Document Externe Link
                    CASE WHEN pt.x_studio_ce_document IS NOT NULL THEN
                        'https://www.chameleonstars.com/web/content/' || pt.x_studio_ce_document || '?model=documents.document&download=true'
                    ELSE NULL END AS ce_document,

                    -- Categorie Namen via de gedeelde tabel
                    cat_bol.x_name ->> 'fr_FR' AS bol_category,
                    cat_kauf.x_name ->> 'fr_FR' AS kaufland_category

                FROM product_template pt
                LEFT JOIN product_product pp ON pp.product_tmpl_id = pt.id
                LEFT JOIN stock_quant sq ON sq.product_id = pp.id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN ordered_images oi ON oi.product_tmpl_id = pt.id
                
                -- Join voor Bol categorie
                LEFT JOIN x_marketplace_categori cat_bol 
                    ON cat_bol.id = pt.x_studio_bol_category
                
                -- Join voor Kaufland categorie
                LEFT JOIN x_marketplace_categori cat_kauf 
                    ON cat_kauf.id = pt.x_studio_kaufland_category
                
                WHERE pt.active = TRUE
                GROUP BY
                    pt.id, pp.id, pt.default_code, pp.barcode, pt.list_price, pc.complete_name, 
                    pt.name, pt.description_ecommerce, pt.x_studio_leeftijd_van, 
                    pt.x_studio_leeftijd_tot, pt.x_studio_ce_document,
                    cat_bol.x_name, cat_kauf.x_name
            )
        """ % self._table)