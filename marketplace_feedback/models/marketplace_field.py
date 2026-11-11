import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .field_suggestions import CODE_NAMES, SUGGESTIONS

_logger = logging.getLogger(__name__)

MARKETPLACES = [("amazon", "Amazon")]

# Vinkje op de property-rij (x_product_property_val) per marktplaats
FLAG_FIELDS = {"amazon": ("x_for_amazon", "Voor Amazon")}

DECISIONS = [
    ("todo", "Te beslissen"),
    ("property", "Property op het artikel"),
    ("odoo", "Ander gegeven in Odoo"),
    ("channable", "Opgelost in Channable"),
    ("manual", "Handmatig (Seller Central)"),
    ("ignore", "Negeren"),
]


def normalize_key(name):
    return " ".join((name or "").split()).lower()


class MarketplaceField(models.Model):
    _name = "marketplace.field"
    _description = "Marktplaatsveld"
    _order = "decision_sequence, issue_count desc, name"

    active = fields.Boolean(default=True)
    marketplace = fields.Selection(MARKETPLACES, "Marktplaats", required=True, default="amazon")
    key = fields.Char(
        "Sleutel", required=True, index=True,
        help="Veldnaam in kleine letters, of 'code:<foutcode>' voor meldingen zonder veld.",
    )
    name = fields.Char("Veld bij de marktplaats", required=True)
    decision = fields.Selection(DECISIONS, "Beslissing", required=True, default="todo")
    decision_sequence = fields.Integer(compute="_compute_decision_sequence", store=True)
    property_id = fields.Many2one(
        "x_product_property_def", "Property", ondelete="set null",
        context={"active_test": False},
    )
    new_property_name = fields.Char(
        "Nieuwe property",
        help="Naam van de property die aangemaakt wordt met 'Properties aanmaken'.",
    )
    note = fields.Text("Wat te doen / hoe opgelost")
    channable_done = fields.Boolean(
        "Ingesteld in Channable",
        help="Vink aan zodra het veld in Channable gekoppeld is (of de regel/vaste waarde staat).",
    )
    error_codes = fields.Char("Foutcodes", readonly=True)
    example_message = fields.Char("Voorbeeldmelding", readonly=True)
    product_types = fields.Char("Amazon-producttypes", readonly=True, help="Bij de laatste import.")
    last_seen = fields.Datetime("Laatst gemeld", readonly=True)
    issue_ids = fields.One2many("marketplace.issue", "field_id", "Meldingen")
    issue_count = fields.Integer("Artikels", compute="_compute_issue_count", store=True)

    _sql_constraints = [
        ("key_uniq", "unique(marketplace, key)", "Dit veld bestaat al voor deze marktplaats."),
    ]

    @api.depends("decision")
    def _compute_decision_sequence(self):
        order = {code: i for i, (code, _label) in enumerate(DECISIONS)}
        for rec in self:
            rec.decision_sequence = order.get(rec.decision, 99)

    @api.depends("issue_ids")
    def _compute_issue_count(self):
        data = self.env["marketplace.issue"]._read_group(
            [("field_id", "in", self.ids), ("product_tmpl_id", "!=", False)],
            ["field_id"], ["product_tmpl_id:count_distinct"],
        )
        counts = {field.id: count for field, count in data}
        for rec in self:
            rec.issue_count = counts.get(rec.id, 0)

    @api.onchange("decision")
    def _onchange_decision(self):
        if self.decision == "property" and not self.property_id and not self.new_property_name:
            self.new_property_name = self.name

    # ------------------------------------------------------------------
    # Wijzigen -> artikels bijwerken
    # ------------------------------------------------------------------
    def write(self, vals):
        res = super().write(vals)
        if {"decision", "property_id"} & set(vals) and not self.env.context.get("marketplace_no_apply"):
            self.filtered(lambda f: f.decision == "property" and f.property_id)._apply_to_articles()
        return res

    def _apply_to_articles(self):
        """Zorg dat elk artikel met een melding voor dit veld een property-rij heeft,
        en zet het vinkje 'Voor <marktplaats>' op die rij."""
        Value = self.env["x_product_property_val"].sudo().with_context(active_test=False)
        created = flagged = 0
        for rec in self:
            if rec.decision != "property" or not rec.property_id:
                continue
            flag = self._flag_field(rec.marketplace)
            templates = rec.issue_ids.product_tmpl_id
            if not templates:
                continue
            existing = Value.search([("x_product", "in", templates.ids), ("x_property", "=", rec.property_id.id)])
            by_tmpl = {}
            for val in existing:
                by_tmpl.setdefault(val.x_product.id, val)
            to_flag = Value.browse([v.id for v in by_tmpl.values() if flag and not v[flag]])
            if to_flag:
                to_flag.write({flag: True})
                flagged += len(to_flag)
            new = [tmpl for tmpl in templates if tmpl.id not in by_tmpl]
            if new:
                vals = {"x_property": rec.property_id.id}
                if flag:
                    vals[flag] = True
                if "x_active" in Value._fields:
                    vals["x_active"] = True
                Value.create([dict(vals, x_product=tmpl.id) for tmpl in new])
                created += len(new)
        return created, flagged

    # ------------------------------------------------------------------
    # Knoppen
    # ------------------------------------------------------------------
    def action_create_properties(self):
        """Maak de voorgestelde properties aan en koppel ze."""
        records = self or self.search([("decision", "=", "property"), ("property_id", "=", False)])
        PropertyDef = self.env["x_product_property_def"].sudo().with_context(active_test=False)
        created = []
        for rec in records.filtered(lambda r: r.decision == "property" and not r.property_id):
            name = (rec.new_property_name or rec.name or "").strip()
            if not name:
                continue
            prop = self._find_property(name)
            if not prop:
                vals = {"x_name": name}
                if "x_active" in PropertyDef._fields:
                    vals["x_active"] = True
                prop = PropertyDef.create(vals)
                created.append(name)
            rec.write({"property_id": prop.id})
            # Andere velden met dezelfde voorgestelde property meteen mee koppelen
            for twin in records.filtered(
                lambda r: not r.property_id and r.decision == "property"
                and normalize_key(r.new_property_name) == normalize_key(name)
            ):
                twin.write({"property_id": prop.id})
        if not created and not records.filtered(lambda r: r.decision == "property"):
            raise UserError(_("Geen velden met beslissing 'Property op het artikel' zonder property."))
        return self._notify(
            _("Properties"),
            _("Aangemaakt: %s", ", ".join(created)) if created else _("Alle properties bestonden al; ze zijn gekoppeld."),
        )

    def action_apply(self):
        records = self or self.search([("decision", "=", "property"), ("property_id", "!=", False)])
        created, flagged = records._apply_to_articles()
        return self._notify(
            _("Artikels bijgewerkt"),
            _("%(created)s property-rijen aangemaakt, %(flagged)s bestaande rijen aangevinkt.",
              created=created, flagged=flagged),
        )

    def action_show_issues(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("marketplace_feedback.action_marketplace_issue")
        action["domain"] = [("field_id", "=", self.id)]
        action["context"] = {}
        action["name"] = self.name
        return action

    def _notify(self, title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": title, "message": message, "sticky": False,
                       "next": {"type": "ir.actions.client", "tag": "soft_reload"}},
        }

    # ------------------------------------------------------------------
    # Hulpfuncties
    # ------------------------------------------------------------------
    @api.model
    def _flag_field(self, marketplace):
        name = FLAG_FIELDS.get(marketplace, (None,))[0]
        return name if name and name in self.env["x_product_property_val"]._fields else None

    @api.model
    def _ensure_flag_fields(self):
        """Maak het vinkje 'Voor Amazon' aan op x_product_property_val, zoals Studio dat
        zou doen (een aangepast veld). Een Python-module kan een Studio-model niet erven."""
        model = self.env["ir.model"].sudo().search([("model", "=", "x_product_property_val")], limit=1)
        if not model:
            _logger.warning("Marktplaatsfeedback: model x_product_property_val niet gevonden.")
            return
        for name, label in FLAG_FIELDS.values():
            if not self.env["ir.model.fields"].sudo().search([("model_id", "=", model.id), ("name", "=", name)]):
                self.env["ir.model.fields"].sudo().create({
                    "model_id": model.id,
                    "name": name,
                    "field_description": label,
                    "ttype": "boolean",
                    "state": "manual",
                    "help": "Deze property is nodig voor deze marktplaats (gemeld in de feedback).",
                })
                _logger.info("Marktplaatsfeedback: veld %s aangemaakt op x_product_property_val.", name)

    @api.model
    def _find_property(self, name):
        """Property-definitie op naam, in elke geïnstalleerde taal, hoofdletters maken niet uit."""
        PropertyDef = self.env["x_product_property_def"].sudo().with_context(active_test=False)
        wanted = normalize_key(name)
        if not wanted:
            return PropertyDef
        installed = [code for code, _label in self.env["res.lang"].get_installed()]
        langs = ["en_US"] + [lang for lang in installed if lang != "en_US"]
        for lang in langs:
            for prop in PropertyDef.with_context(lang=lang).search([]):
                if normalize_key(prop.x_name) == wanted:
                    return prop.with_context(lang=None)
        return PropertyDef

    @api.model
    def _suggestion_vals(self, key, name):
        """Beslissing, property en toelichting voor een nieuw veld."""
        decision, prop_name, new_prop, note = SUGGESTIONS.get(key, ("todo", None, None, None))
        vals = {"decision": decision, "note": note or False}
        if decision == "property":
            prop = self._find_property(prop_name or new_prop or name)
            if prop:
                vals["property_id"] = prop.id
            else:
                vals["new_property_name"] = new_prop or prop_name or name
        elif decision == "todo":
            # Bestaat er een property met precies dezelfde naam? Dan is dat het voorstel.
            prop = self._find_property(name)
            if prop:
                vals.update(decision="property", property_id=prop.id)
        return vals

    @api.model
    def _get_or_create(self, marketplace, key, name):
        rec = self.with_context(active_test=False).search(
            [("marketplace", "=", marketplace), ("key", "=", key)], limit=1)
        if rec:
            return rec, False
        vals = {"marketplace": marketplace, "key": key, "name": name}
        vals.update(self._suggestion_vals(key, name))
        return self.with_context(marketplace_no_apply=True).create(vals), True

    @api.model
    def _load_suggestions(self):
        """Bij installatie: de gekende velden uit de Amazon-run alvast in de lijst."""
        for key in SUGGESTIONS:
            if key.startswith("code:"):
                code = key[5:]
                name = "%s (%s)" % (CODE_NAMES.get(code, code), code)
            else:
                name = next((n for n in _DISPLAY_NAMES if normalize_key(n) == key), key)
            self._get_or_create("amazon", key, name)


# Weergavenamen zoals Amazon ze schrijft (voor de lijst bij installatie)
_DISPLAY_NAMES = [
    "Brand Name", "Manufacturer", "Target Audience Keyword", "Manufacturer Minimum Age (MONTHS)",
    "Manufacturer Maximum Age (MONTHS)", "Age Range Description", "EU Toys Safety Directive Age Warning",
    "EU TSD Non Age Specific Warning", "EU Toys Safety Directive Language", "Safety Warning",
    "Included Components", "Material", "Material Composition", "Color", "Language", "Item Height",
    "Item Height Unit", "Item Length", "Item length Unit", "Item depth Unit", "Item Width", "Item Width Unit",
    "Required Assembly", "Are batteries required?", "Battery Installation Device Type",
    "Lithium Battery Weight", "Battery Weight", "Lithium Battery Energy Content", "Hazmat", "Magnification Maximum Unit", "Minimum Focal Length Unit",
    "Item Name", "Model Name", "Product Description", "Bullet Point", "List Price", "Part Number",
    "Model Number", "External Product ID", "Category", "Item Weight", "Item Weight Unit", "Package Weight",
    "Package Weight Unit", "Package Height Unit", "Quantity", "Recommended Browse Nodes", "Country of Origin",
    "Dangerous Goods Regulations", "Warranty Description", "Unit Count", "Number of Items", "Number of Boxes",
    "Power Plug", "Accepted Voltage Frequency", "Power Source", "Contains food or beverage?",
    "Is Product Expirable", "Is the Item Heat Sensitive?", "Is Fragile?", "GDPR Risk", "Subject Keyword",
    "Size", "Department Name", "Metal Type", "Gem Type", "Ink Base", "Maximum Order Quantity", "parentage_level",
]
