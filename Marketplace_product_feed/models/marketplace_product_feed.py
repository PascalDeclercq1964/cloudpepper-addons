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
    name_it = fields.Char(readonly=True)
    name_es = fields.Char(readonly=True)
    description_nl = fields.Html(readonly=True)
    description_fr = fields.Html(readonly=True)
    description_de = fields.Html(readonly=True)
    description_en = fields.Html(readonly=True)
    description_it = fields.Html(readonly=True)
    description_es = fields.Html(readonly=True)
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

    # Basisgegevens (v1.0.14)
    weight_kg = fields.Float(readonly=True)
    weight_g = fields.Integer(readonly=True)
    volume_m3 = fields.Float(readonly=True)
    country_of_origin = fields.Char(readonly=True)
    hs_code = fields.Char(readonly=True)
    box_length_cm = fields.Float(readonly=True)
    box_width_cm = fields.Float(readonly=True)
    box_height_cm = fields.Float(readonly=True)
    mounted_length_cm = fields.Float(readonly=True)
    mounted_width_cm = fields.Float(readonly=True)
    mounted_height_cm = fields.Float(readonly=True)
    age_from_months = fields.Integer(readonly=True)
    age_to_months = fields.Integer(readonly=True)
    players_min = fields.Integer(readonly=True)
    players_max = fields.Integer(readonly=True)
    search_terms_nl = fields.Char(readonly=True)
    search_terms_fr = fields.Char(readonly=True)
    search_terms_de = fields.Char(readonly=True)
    search_terms_en = fields.Char(readonly=True)
    search_terms_it = fields.Char(readonly=True)
    search_terms_es = fields.Char(readonly=True)

    # LET OP: init() moet IN de klasse staan (ingesprongen). Staat ze ernaast,
    # dan voert Odoo ze nooit uit en verandert een module-update de view niet.
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
                    -- Nooit negatief: marktplaatsen weigeren een negatieve voorraad
                    GREATEST(COALESCE(sq.on_hand, 0), 0) AS qty_available,
                    pc.complete_name AS category_name,

                    -- Productvertalingen (leeg als de vertaling ontbreekt)
                    replace(pt.name ->> 'nl_NL', ';', ' ')::text AS name_nl,
                    replace(pt.name ->> 'fr_FR', ';', ' ')::text AS name_fr,
                    replace(pt.name ->> 'de_DE', ';', ' ')::text AS name_de,
                    replace(pt.name ->> 'en_US', ';', ' ')::text AS name_en,
                    replace(pt.name ->> 'it_IT', ';', ' ')::text AS name_it,
                    replace(pt.name ->> 'es_ES', ';', ' ')::text AS name_es,
                    replace(pt.description_ecommerce ->> 'nl_NL', ';', '')::text AS description_nl,
                    replace(pt.description_ecommerce ->> 'fr_FR', ';', '')::text AS description_fr,
                    replace(pt.description_ecommerce ->> 'de_DE', ';', '')::text AS description_de,
                    replace(pt.description_ecommerce ->> 'en_US', ';', '')::text AS description_en,
                    replace(pt.description_ecommerce ->> 'it_IT', ';', '')::text AS description_it,
                    replace(pt.description_ecommerce ->> 'es_ES', ';', '')::text AS description_es,

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

                    -- Productgroep (veld 'Product group' op het product; basis voor de categorieregels in Channable)
                    COALESCE(cat_pg.x_name ->> 'fr_FR', cat_pg.x_name ->> 'nl_NL', cat_pg.x_name ->> 'en_US') AS product_group,

                    ( SELECT jsonb_object_agg(lower(def.x_name ->> 'en_US'), replace(val.x_value,';', '|'))
                        FROM x_product_property_val val
                        JOIN x_product_property_def def ON val.x_property = def.id
                        WHERE val.x_product = pt.id
                        )::text AS product_properties,

                    -- Gewicht en volume (Odoo: kg en m³; leeg als niet ingevuld)
                    NULLIF(pp.weight, 0) AS weight_kg,
                    NULLIF(ROUND(pp.weight * 1000), 0)::integer AS weight_g,
                    NULLIF(pp.volume, 0) AS volume_m3,

                    -- Douane: land van oorsprong (ISO-code, bv. CN) en HS-code
                    rc.code AS country_of_origin,
                    NULLIF(pt.hs_code, '') AS hs_code,

                    -- Afmetingen verpakking en gemonteerd product (in Odoo in meter, hier in cm)
                    NULLIF(ROUND((pt.x_studio_length_box * 100)::numeric, 1), 0) AS box_length_cm,
                    NULLIF(ROUND((pt.x_studio_width_box * 100)::numeric, 1), 0) AS box_width_cm,
                    NULLIF(ROUND((pt.x_studio_height_box * 100)::numeric, 1), 0) AS box_height_cm,
                    NULLIF(ROUND((pt.x_studio_length_mounted * 100)::numeric, 1), 0) AS mounted_length_cm,
                    NULLIF(ROUND((pt.x_studio_width_mounted * 100)::numeric, 1), 0) AS mounted_width_cm,
                    NULLIF(ROUND((pt.x_studio_height_mounted * 100)::numeric, 1), 0) AS mounted_height_cm,

                    -- Leeftijd (velden 'Leeftijd van/tot' op het product, in maanden)
                    pt.x_studio_leeftijd_van AS age_from_months,
                    pt.x_studio_leeftijd_tot AS age_to_months,

                    -- Aantal spelers en zoektermen
                    NULLIF(pt.x_studio_playercountmin, 0) AS players_min,
                    NULLIF(pt.x_studio_playercountmax, 0) AS players_max,
                    -- Zoektermen is een vertaalbaar veld (jsonb): één kolom per taal, zoals de namen
                    NULLIF(replace(pt.x_studio_searchterms ->> 'nl_NL', ';', ','), '') AS search_terms_nl,
                    NULLIF(replace(pt.x_studio_searchterms ->> 'fr_FR', ';', ','), '') AS search_terms_fr,
                    NULLIF(replace(pt.x_studio_searchterms ->> 'de_DE', ';', ','), '') AS search_terms_de,
                    NULLIF(replace(pt.x_studio_searchterms ->> 'en_US', ';', ','), '') AS search_terms_en,
                    NULLIF(replace(pt.x_studio_searchterms ->> 'it_IT', ';', ','), '') AS search_terms_it,
                    NULLIF(replace(pt.x_studio_searchterms ->> 'es_ES', ';', ','), '') AS search_terms_es


                FROM product_product pp
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN res_country rc ON rc.id = pt.country_of_origin

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
                LEFT JOIN x_marketplace_categori cat_pg ON cat_pg.id = pt.x_studio_product_group

                WHERE pp.active = TRUE
                  AND pt.active = TRUE
                  AND pp.barcode IS NOT NULL
            )
        """ % self._table)
