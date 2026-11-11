from odoo import api, fields, models

from .marketplace_field import MARKETPLACES

PLACEHOLDERS = ("", "undefined")


class MarketplaceIssue(models.Model):
    _name = "marketplace.issue"
    _description = "Melding van een marktplaats"
    _order = "field_id, product_tmpl_id, id"
    _rec_name = "field_id"

    import_id = fields.Many2one("marketplace.feedback.import", "Import", ondelete="cascade", index=True)
    marketplace = fields.Selection(MARKETPLACES, "Marktplaats", required=True, default="amazon")
    field_id = fields.Many2one("marketplace.field", "Veld", required=True, ondelete="cascade", index=True)
    decision = fields.Selection(related="field_id.decision", store=True, string="Beslissing")
    property_id = fields.Many2one(related="field_id.property_id", string="Property")
    note = fields.Text(related="field_id.note", string="Wat te doen")
    product_tmpl_id = fields.Many2one("product.template", "Product", index=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", "Variant", ondelete="cascade")
    client_ids = fields.Char("Channable-id", help="Id('s) van het artikel in Channable (interne referentie).")
    ean = fields.Char("EAN")
    amazon_product_type = fields.Char("Amazon-producttype")
    error_code = fields.Char("Foutcode")
    level = fields.Selection([("error", "Fout"), ("warning", "Waarschuwing")], "Niveau", default="error")
    message = fields.Text("Melding")
    property_value = fields.Char(
        "Waarde", compute="_compute_property_value", inverse="_inverse_property_value",
        help="Waarde van de property op het artikel. Hier invullen = op het artikel bewaren.",
    )
    value_missing = fields.Boolean(
        "Waarde ontbreekt", compute="_compute_property_value", search="_search_value_missing",
    )

    # ------------------------------------------------------------------
    # Waarde van de property (lezen en schrijven op het artikel)
    # ------------------------------------------------------------------
    def _value_rows(self):
        """{(template_id, property_id): x_product_property_val}"""
        pairs = {(i.product_tmpl_id.id, i.property_id.id) for i in self if i.product_tmpl_id and i.property_id}
        if not pairs:
            return {}
        Value = self.env["x_product_property_val"].sudo().with_context(active_test=False)
        rows = Value.search([
            ("x_product", "in", list({p[0] for p in pairs})),
            ("x_property", "in", list({p[1] for p in pairs})),
        ])
        result = {}
        for row in rows:
            key = (row.x_product.id, row.x_property.id)
            # Een ingevulde rij gaat voor op een lege
            if key not in result or (not _filled(result[key].x_value) and _filled(row.x_value)):
                result[key] = row
        return result

    @api.depends("product_tmpl_id", "field_id.property_id")
    def _compute_property_value(self):
        rows = self._value_rows()
        for issue in self:
            row = rows.get((issue.product_tmpl_id.id, issue.property_id.id))
            value = row.x_value if row else False
            issue.property_value = value or False
            issue.value_missing = bool(issue.property_id and issue.product_tmpl_id and not _filled(value))

    def _inverse_property_value(self):
        Value = self.env["x_product_property_val"].with_context(active_test=False)
        rows = self._value_rows()
        for issue in self:
            if not (issue.product_tmpl_id and issue.property_id):
                continue
            value = (issue.property_value or "").strip() or False
            row = rows.get((issue.product_tmpl_id.id, issue.property_id.id))
            flag = self.env["marketplace.field"]._flag_field(issue.marketplace)
            vals = {"x_value": value}
            if flag:
                vals[flag] = True
            if row:
                row.write(vals)
            elif value:
                vals.update(x_product=issue.product_tmpl_id.id, x_property=issue.property_id.id)
                if "x_active" in Value._fields:
                    vals["x_active"] = True
                rows[(issue.product_tmpl_id.id, issue.property_id.id)] = Value.create(vals)

    def _search_value_missing(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            return [("id", "=", 0)]
        missing = (operator == "=") == value
        self.env["x_product_property_val"].flush_model(["x_product", "x_property", "x_value"])
        self.env["marketplace.field"].flush_model(["property_id"])
        self.flush_model(["product_tmpl_id", "field_id"])
        self.env.cr.execute(
            """
            SELECT i.id
              FROM marketplace_issue i
              JOIN marketplace_field f ON f.id = i.field_id
             WHERE i.product_tmpl_id IS NOT NULL
               AND f.property_id IS NOT NULL
               AND NOT EXISTS (
                     SELECT 1 FROM x_product_property_val v
                      WHERE v.x_product = i.product_tmpl_id
                        AND v.x_property = f.property_id
                        AND lower(trim(coalesce(v.x_value, ''))) NOT IN %s)
            """,
            [PLACEHOLDERS],
        )
        ids = [row[0] for row in self.env.cr.fetchall()]
        return [("id", "in" if missing else "not in", ids)]

    def action_open_product(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.template",
            "res_id": self.product_tmpl_id.id,
            "view_mode": "form",
        }


def _filled(value):
    return bool(value) and str(value).strip().lower() not in PLACEHOLDERS
