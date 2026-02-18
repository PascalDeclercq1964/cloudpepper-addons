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
    main_image = fields.Char(readonly=True)
    image_1 = fields.Char(readonly=True)
    image_2 = fields.Char(readonly=True)
    image_3 = fields.Char(readonly=True)
    image_4 = fields.Char(readonly=True)
    image_5 = fields.Char(readonly=True)
    
    ce_document = fields.Char(readonly=True)
    bol_category = fields.Char(readonly=True)
    kaufland_category = fields.Char(readonly=True)
    cdiscount_category = fields.Char(readonly=True)
    product_group = fields.Char(readonly=True)
    product_properties = fields.Char(readonly=True)

def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    pp.id AS id,
                    pp.id AS product_product_id,
                    COALESCE(pp.default_code, pt.default_code) AS sku,
                    pp.barcode AS barcode,
                    pt.list_price AS price,
                    COALESCE(sq.on_hand, 0) AS qty_available,
                    pc.complete_name AS category_name,
                    
                    -- Productvertalingen
                    pt.name ->> 'nl_NL' AS name_nl,
                    pt.name ->> 'fr_FR' AS name_fr,
                    pt.name ->> 'de_DE' AS name_de,
                    pt.name ->> 'en_US' AS name_en,
                    pt.description_ecommerce ->> 'nl_NL' AS description_nl,
                    pt.description_ecommerce ->> 'fr_FR' AS description_fr,
                    pt.description_ecommerce ->> 'de_DE' AS description_de,
                    pt.description_ecommerce ->> 'en_US' AS description_en,
                    
                    'https://www.chameleonstars.com/shop/product/' || pt.id AS product_url,
                    
                    -- De hoofdafbeelding (rechtsboven op productniveau)
                    'https://www.chameleonstars.com/web/image/product.template/' || pt.id || '/image_1920' AS main_image,
                    -- Afbeeldingen (Subqueries)
                    (SELECT 'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920'
                     FROM product_image pi WHERE pi.product_tmpl_id = pt.id ORDER BY pi.sequence, pi.id LIMIT 1 OFFSET 0) AS image_1,
                    (SELECT 'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920'
                     FROM product_image pi WHERE pi.product_tmpl_id = pt.id ORDER BY pi.sequence, pi.id LIMIT 1 OFFSET 1) AS image_2,
                    (SELECT 'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920'
                     FROM product_image pi WHERE pi.product_tmpl_id = pt.id ORDER BY pi.sequence, pi.id LIMIT 1 OFFSET 2) AS image_3,
                    (SELECT 'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920'
                     FROM product_image pi WHERE pi.product_tmpl_id = pt.id ORDER BY pi.sequence, pi.id LIMIT 1 OFFSET 3) AS image_4,
                    (SELECT 'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920'
                     FROM product_image pi WHERE pi.product_tmpl_id = pt.id ORDER BY pi.sequence, pi.id LIMIT 1 OFFSET 4) AS image_5,

                    -- CE Document
                    CASE WHEN pt.x_studio_ce_document IS NOT NULL THEN
                        'https://www.chameleonstars.com/web/content/' || pt.x_studio_ce_document || '?model=documents.document&download=true'
                    ELSE NULL END AS ce_document,

                    -- Categorieën (fr_FR met fallback)
                    COALESCE(cat_bol.x_name ->> 'fr_FR', cat_bol.x_name ->> 'nl_NL') AS bol_category,
                    COALESCE(cat_kauf.x_name ->> 'fr_FR', cat_kauf.x_name ->> 'nl_NL') AS kaufland_category,
                    COALESCE(cat_cdisc.x_name ->> 'fr_FR', cat_cdisc.x_name ->> 'nl_NL') AS cdiscount_category,

                    ( SELECT jsonb_object_agg(lower(def.x_name ->> 'en_US'), replace(val.x_value,';', '|'))
                        FROM x_product_property_val val
                        JOIN x_product_property_def def ON val.x_property = def.id
                        WHERE val.x_product = pt.id
                        )::text AS product_properties


                FROM product_product pp
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                
                -- Voorraad
                LEFT JOIN (
                    SELECT q.product_id, SUM(q.quantity) AS on_hand
                    FROM stock_quant q
                    JOIN stock_location l ON q.location_id = l.id
                    WHERE l.usage = 'internal'
                    GROUP BY q.product_id
                ) sq ON sq.product_id = pp.id
                
                -- Categorie Joins
                LEFT JOIN x_marketplace_categori cat_bol ON cat_bol.id = pt.x_studio_bol_category
                LEFT JOIN x_marketplace_categori cat_kauf ON cat_kauf.id = pt.x_studio_kaufland_category
                LEFT JOIN x_marketplace_categori cat_cdisc ON cat_cdisc.id = pt.x_studio_cdiscount_category
                
                -- Attribuut Joins voor de Many2one velden
                LEFT JOIN product_attribute_value pav_age ON pav_age.id = pt.x_studio_recommendedage
                LEFT JOIN product_attribute_value pav_batt ON pav_batt.id = pt.x_studio_battery_type
                
                WHERE pp.active = TRUE 
                  AND pt.active = TRUE 
                  AND pp.barcode IS NOT NULL
            )
        """ % self._table)