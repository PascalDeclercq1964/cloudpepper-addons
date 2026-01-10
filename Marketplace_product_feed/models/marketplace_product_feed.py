from odoo import models, fields, tools

class MarketplaceProductFeed(models.Model):
    _name = "x_marketplace.product.feed"
    _description = "Marketplace Product Feed"
    _auto = False
    _table='marketplace_product_feed'
    _rec_name = "sku"

    id=fields.Integer(readonly=True)
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

    def init(self):
        # Dit zorgt ervoor dat Odoo weet dat de view bestaat
        # Je kan hier je eigen SQL voor de view plaatsen
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            WITH ordered_images AS (
                SELECT
                    pi.product_tmpl_id,
                    pi.id,
                    'https://www.chameleonstars.com/web/image/product.image/' || pi.id || '/image_1920' AS url,
                    ROW_NUMBER() OVER (
                        PARTITION BY pi.product_tmpl_id
                        ORDER BY pi.sequence, pi.id
                    ) AS rn
                FROM product_image pi
            )
            SELECT
                pt.id,
                pp.id AS product_product_id,

                -- Identiteit
                pt.default_code AS sku,
                MIN(pp.barcode) AS barcode,

                -- Prijs & stock
                pt.list_price AS price,
                COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS qty_available,

                -- Categorie
                pc.complete_name AS category_name,

                -- Namen per taal (JSON)
                pt.name ->> 'nl_BE' AS name_nl,
                pt.name ->> 'fr_FR' AS name_fr,
                pt.name ->> 'de_DE' AS name_de,
                pt.name ->> 'en_US' AS name_en,

                -- E-commerce beschrijvingen per taal
                pt.description_ecommerce ->> 'nl_BE' AS description_nl,
                pt.description_ecommerce ->> 'fr_FR' AS description_fr,
                pt.description_ecommerce ->> 'de_DE' AS description_de,
                pt.description_ecommerce ->> 'en_US' AS description_en,

                -- Product URL
                '/shop/product/' || pt.id AS product_url,

                -- Max 5 afbeeldingen
                MAX(CASE WHEN oi.rn = 1 THEN oi.url END) AS image_1,
                MAX(CASE WHEN oi.rn = 2 THEN oi.url END) AS image_2,
                MAX(CASE WHEN oi.rn = 3 THEN oi.url END) AS image_3,
                MAX(CASE WHEN oi.rn = 4 THEN oi.url END) AS image_4,
                MAX(CASE WHEN oi.rn = 5 THEN oi.url END) AS image_5

            FROM product_template pt
            LEFT JOIN product_product pp
                ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_quant sq
                ON sq.product_id = pp.id
            LEFT JOIN product_category pc
                ON pc.id = pt.categ_id
            LEFT JOIN ordered_images oi
                ON oi.product_tmpl_id = pt.id
            WHERE pt.active = TRUE
            GROUP BY
                pt.id,
                product_product_id,
                pt.default_code,
                pt.list_price,
                pc.complete_name,
                pt.name,
                pt.description_ecommerce;
        """ % self._table)
