import base64
import csv
import io
import logging
import re

from odoo import _, fields, models
from odoo.exceptions import UserError

from .field_suggestions import CODE_NAMES
from .marketplace_field import MARKETPLACES, normalize_key

_logger = logging.getLogger(__name__)

# Veldnaam uit de melding van Amazon halen
FIELD_PATTERNS = [
    re.compile(r"for the attribute '([^']+)'"),
    re.compile(r"for attribute '([^']+)'"),
    re.compile(r"^'([^']+)' is required but missing"),
    re.compile(r"[Vv]alue (?:provided )?for '([^']+)'"),
    re.compile(r"^Attribute (\S+) is missing"),
    re.compile(r"^([A-Za-z][A-Za-z ]*): Input should be"),
]

COLUMNS = {
    "code": "api_error_code",
    "level": "api_error_level",
    "message": "api_error_message",
    "client_id": "client_id",
    "category": "category",
    "ean": "externally_assigned_product_identifier.value",
}


def extract_field(message):
    for pattern in FIELD_PATTERNS:
        match = pattern.search(message or "")
        if match:
            return " ".join(match.group(1).split())
    return None


def short_code(code):
    """'90220 - Submission - ERROR' -> '90220'; 'Channable Validation Error' blijft."""
    code = (code or "").strip()
    first = code.split(" ")[0]
    return first if first.isdigit() else code


class MarketplaceFeedbackImport(models.Model):
    _name = "marketplace.feedback.import"
    _description = "Import van marktplaatsfeedback"
    _order = "create_date desc, id desc"

    name = fields.Char("Bestand", required=True, default=lambda self: _("Feedback"))
    marketplace = fields.Selection(MARKETPLACES, "Marktplaats", required=True, default="amazon")
    file = fields.Binary("Feedback-CSV", attachment=True, required=True,
                         help="In Channable: kanaal › Resultaat › Feedback › 'Download as CSV'.")
    state = fields.Selection([("draft", "Nieuw"), ("done", "Verwerkt")], default="draft", readonly=True)
    processed_on = fields.Datetime("Verwerkt op", readonly=True)
    row_count = fields.Integer("Meldingen", readonly=True)
    item_count = fields.Integer("Artikels in Channable", readonly=True)
    matched_count = fields.Integer("Gevonden in Odoo", readonly=True)
    new_field_count = fields.Integer("Nieuwe velden", readonly=True)
    value_rows_created = fields.Integer("Property-rijen aangemaakt", readonly=True)
    unmatched = fields.Text("Niet gevonden in Odoo", readonly=True,
                            help="Channable-id en EAN van artikels zonder product in Odoo.")
    issue_ids = fields.One2many("marketplace.issue", "import_id", "Meldingen van deze import")

    def action_process(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Kies eerst het CSV-bestand."))
        newer = self.search([("marketplace", "=", self.marketplace), ("state", "=", "done"),
                             ("id", ">", self.id)], limit=1)
        if newer:
            raise UserError(_("Er is al een recentere import (%s). Een oudere import opnieuw verwerken "
                              "zou de nieuwere feedback overschrijven.", newer.name))
        rows = self._read_rows()
        Field = self.env["marketplace.field"]
        Issue = self.env["marketplace.issue"]

        products = self._match_products(rows)
        fields_by_key, new_fields, types_by_field, codes_by_field = {}, Field, {}, {}
        issues = {}
        unmatched = {}
        for row in rows:
            message = (row.get(COLUMNS["message"]) or "").strip()
            code = short_code(row.get(COLUMNS["code"]))
            field_name = extract_field(message)
            if field_name:
                key, name = normalize_key(field_name), field_name
            else:
                key, name = "code:%s" % code, "%s (%s)" % (CODE_NAMES.get(code, message[:60] or code), code)
            if key not in fields_by_key:
                field, is_new = Field._get_or_create(self.marketplace, key, name)
                fields_by_key[key] = field
                if is_new:
                    new_fields |= field
            field = fields_by_key[key]
            client_id = (row.get(COLUMNS["client_id"]) or "").strip()
            ean = (row.get(COLUMNS["ean"]) or "").strip()
            category = (row.get(COLUMNS["category"]) or "").strip()
            if category:
                types_by_field.setdefault(field.id, set()).add(category)
            codes_by_field.setdefault(field.id, set()).add(code)
            product = products.get(client_id) or products.get("ean:" + ean.lstrip("0"))
            if not product:
                unmatched[client_id or ean] = ean
            tmpl_id = product.product_tmpl_id.id if product else False
            # Eén melding per artikel (template), veld en code; varianten worden samengevoegd
            ikey = (tmpl_id or "x:" + (client_id or ean), field.id, code)
            issue = issues.get(ikey)
            if issue:
                if client_id and client_id not in issue["client_ids"]:
                    issue["client_ids"].append(client_id)
                continue
            # Het niveau staat in de foutcode ('... - Listing state - WARNING')
            raw_code = row.get(COLUMNS["code"]) or ""
            is_warning = "WARNING" in raw_code.upper() or (row.get(COLUMNS["level"]) or "").lower() == "warning"
            issues[ikey] = {
                "import_id": self.id,
                "marketplace": self.marketplace,
                "field_id": field.id,
                "product_tmpl_id": tmpl_id,
                "product_id": product.id if product else False,
                "client_ids": [client_id] if client_id else [],
                "ean": ean or False,
                "amazon_product_type": category or False,
                "error_code": code,
                "level": "warning" if is_warning else "error",
                "message": message,
            }

        # De vorige stand van deze marktplaats vervangen door de nieuwe
        Issue.search([("marketplace", "=", self.marketplace)]).unlink()
        for vals in issues.values():
            vals["client_ids"] = ", ".join(vals["client_ids"]) or False
        Issue.create(list(issues.values()))

        now = fields.Datetime.now()
        for field in fields_by_key.values():
            example = next((v["message"] for v in issues.values() if v["field_id"] == field.id), False)
            field.with_context(marketplace_no_apply=True).write({
                "last_seen": now,
                "product_types": ", ".join(sorted(types_by_field.get(field.id, []))) or False,
                "error_codes": ", ".join(sorted(codes_by_field.get(field.id, []))),
                "example_message": (example or "")[:250] or False,
                "active": True,
            })
        created, _flagged = Field.browse([f.id for f in fields_by_key.values()])._apply_to_articles()

        self.write({
            "state": "done",
            "processed_on": now,
            "row_count": len(rows),
            "item_count": len({(r.get(COLUMNS["client_id"]) or r.get(COLUMNS["ean"]) or "") for r in rows}),
            "matched_count": len({p.id for p in products.values()}),
            "new_field_count": len(new_fields),
            "value_rows_created": created,
            "unmatched": "\n".join(
                "%s (EAN %s)" % (cid, ean) if ean and ean != cid else cid
                for cid, ean in sorted(unmatched.items())
            ) or False,
        })
        return True

    # ------------------------------------------------------------------
    def _read_rows(self):
        raw = base64.b64decode(self.file)
        for encoding in ("utf-8-sig", "cp1252"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        # Scheidingsteken uit de kopregel (Channable gebruikt komma's; Excel soms ';')
        header = text.split("\n", 1)[0]
        delimiter = max([",", ";", "\t"], key=header.count)
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
        missing = {COLUMNS["code"], COLUMNS["message"], COLUMNS["client_id"]} - set(reader.fieldnames or [])
        if missing:
            raise UserError(_(
                "Dit lijkt geen Feedback-CSV van Channable: kolommen %s ontbreken.\n"
                "Download het bestand in Channable via Resultaat › Feedback › 'Download as CSV'.",
                ", ".join(sorted(missing)),
            ))
        return list(reader)

    def _match_products(self, rows):
        """{client_id: product.product, 'ean:<zonder voorloopnullen>': product.product}"""
        Product = self.env["product.product"].with_context(active_test=False)
        refs = {(r.get(COLUMNS["client_id"]) or "").strip() for r in rows} - {""}
        eans = {(r.get(COLUMNS["ean"]) or "").strip() for r in rows} - {""}
        result = {}
        for product in Product.search([("default_code", "in", list(refs))]):
            result.setdefault(product.default_code, product)
        stripped = {ean.lstrip("0") for ean in eans}
        candidates = Product.search([("barcode", "!=", False), ("barcode", "in", list(eans | stripped
                                     | {"0" + e for e in stripped}))])
        for product in candidates:
            result.setdefault("ean:" + product.barcode.strip().lstrip("0"), product)
        return result
