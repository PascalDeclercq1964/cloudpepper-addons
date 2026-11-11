import base64
from unittest import SkipTest

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

HEADER = ('"api_error_level","api_error_code","api_error_message","category","client_id",'
          '"externally_assigned_product_identifier.type","externally_assigned_product_identifier.value"\n')


def line(code, message, client_id, ean, category="TOYS_AND_GAMES"):
    message = message.replace('"', '""')
    return f'"error","{code}","{message}","{category}","{client_id}","ean","{ean}"\n'


@tagged("post_install", "-at_install")
class TestMarketplaceFeedback(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for model in ("x_product_property_def", "x_product_property_val"):
            if model not in cls.env:
                raise SkipTest("Studio-model %s ontbreekt" % model)
        cls.Def = cls.env["x_product_property_def"]
        cls.Val = cls.env["x_product_property_val"].with_context(active_test=False)
        cls.Field = cls.env["marketplace.field"]
        cls.material = cls.Field._find_property("Material") or cls.Def.create({"x_name": "Material"})
        cls.toy = cls.env["product.template"].create({
            "name": "Testauto", "default_code": "TST-1", "barcode": "5400000001112", "sale_ok": True})
        cls.doll = cls.env["product.template"].create({
            "name": "Testpop", "default_code": "ANDERE-REF", "barcode": "5400000001129", "sale_ok": True})

    def _import(self, body):
        data = (HEADER + body).encode("utf-8")
        imp = self.env["marketplace.feedback.import"].create(
            {"name": "test.csv", "file": base64.b64encode(data)})
        imp.action_process()
        return imp

    def test_import_creates_issues_and_property_rows(self):
        imp = self._import(
            line("90220 - Submission - ERROR", "'Material' is required but missing.", "TST-1", "5400000001112")
            + line("90220 - Submission - ERROR", "'Warranty Description' is required but missing.", "TST-1", "5400000001112")
            # Pop: niet op referentie, wel op EAN (met voorloopnul)
            + line("90220 - Submission - ERROR", "'Material' is required but missing.", "ONBEKEND", "05400000001129")
            + line("100873 - Listing state - ERROR", "The barcode ... is already assigned to a different ASIN", "XYZ", "123")
        )
        self.assertEqual(imp.row_count, 4)
        self.assertEqual(imp.matched_count, 2)
        self.assertIn("XYZ", imp.unmatched)
        material = self.Field.search([("key", "=", "material")])
        self.assertEqual(material.decision, "property")
        self.assertEqual(material.property_id, self.material)
        self.assertEqual(material.issue_count, 2)
        self.assertEqual(self.Field.search([("key", "=", "warranty description")]).decision, "channable")
        self.assertEqual(self.Field.search([("key", "=", "code:100873")]).decision, "manual")
        # Lege property-rij met vinkje 'Voor Amazon' op beide artikels
        for tmpl in (self.toy, self.doll):
            row = self.Val.search([("x_product", "=", tmpl.id), ("x_property", "=", self.material.id)])
            self.assertEqual(len(row), 1)
            self.assertFalse(row.x_value)
            self.assertTrue(row.x_for_amazon)
        self.assertEqual(self.toy.marketplace_issue_count, 2)
        self.assertEqual(self.toy.marketplace_amazon_type, "TOYS_AND_GAMES")

    def test_existing_value_is_flagged_not_duplicated(self):
        self.Val.create({"x_product": self.toy.id, "x_property": self.material.id, "x_value": "Plastique"})
        self._import(line("90220 - Submission - ERROR", "'Material' is required but missing.", "TST-1", ""))
        row = self.Val.search([("x_product", "=", self.toy.id), ("x_property", "=", self.material.id)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.x_value, "Plastique")
        self.assertTrue(row.x_for_amazon)

    def test_fill_value_from_issue_list(self):
        self._import(line("90220 - Submission - ERROR", "'Material' is required but missing.", "TST-1", ""))
        issue = self.env["marketplace.issue"].search([("product_tmpl_id", "=", self.toy.id)])
        Issue = self.env["marketplace.issue"]
        self.assertIn(issue, Issue.search([("value_missing", "=", True)]))
        issue.property_value = "Bois"
        row = self.Val.search([("x_product", "=", self.toy.id), ("x_property", "=", self.material.id)])
        self.assertEqual(row.x_value, "Bois")
        issue.invalidate_recordset()
        self.assertNotIn(issue, Issue.search([("value_missing", "=", True)]))
        self.assertIn(issue, Issue.search([("value_missing", "=", False)]))

    def test_new_field_create_property_and_apply(self):
        self._import(line("90220 - Submission - ERROR", "'Shiny New Attribute' is required but missing.", "TST-1", ""))
        field = self.Field.search([("key", "=", "shiny new attribute")])
        self.assertEqual(field.decision, "todo")
        # Beslissen: property op het artikel -> voorstel nieuwe naam -> aanmaken
        field.decision = "property"
        field._onchange_decision()
        self.assertEqual(field.new_property_name, "Shiny New Attribute")
        field.new_property_name = "Shiny (Y/N)"
        field.action_create_properties()
        self.assertEqual(field.property_id.x_name, "Shiny (Y/N)")
        row = self.Val.search([("x_product", "=", self.toy.id), ("x_property", "=", field.property_id.id)])
        self.assertTrue(row.x_for_amazon, "de wijziging van de beslissing past de artikels meteen aan")

    def test_reimport_replaces_previous_feedback(self):
        self._import(line("90220 - Submission - ERROR", "'Material' is required but missing.", "TST-1", ""))
        self._import(line("90220 - Submission - ERROR", "'Color' is required but missing.", "ANDERE-REF", ""))
        self.assertFalse(self.toy.marketplace_issue_ids)
        self.assertEqual(self.doll.marketplace_issue_ids.field_id.key, "color")
        # Het vinkje blijft: de property blijft belangrijk voor Amazon
        row = self.Val.search([("x_product", "=", self.toy.id), ("x_property", "=", self.material.id)])
        self.assertTrue(row.x_for_amazon)

    def test_field_name_extraction(self):
        from ..models.marketplace_feedback_import import extract_field
        self.assertEqual(extract_field("'Item Name' is required but missing."), "Item Name")
        self.assertEqual(extract_field(
            "The field 'height.value' for the attribute 'Item Height' does not have enough values."), "Item Height")
        self.assertEqual(extract_field("The provided value for 'Maximum Order Quantity' is invalid."),
                         "Maximum Order Quantity")
        self.assertEqual(extract_field("Attribute parentage_level is missing."), "parentage_level")
        self.assertEqual(extract_field("Category: Input should be a valid string"), "Category")
        self.assertEqual(extract_field("'GDPR  Risk' is required but missing."), "GDPR Risk")
        self.assertIsNone(extract_field("Your image file type isn't supported."))

    def test_wrong_file(self):
        with self.assertRaises(UserError):
            self.env["marketplace.feedback.import"].create(
                {"name": "x.csv", "file": base64.b64encode(b"a,b\n1,2\n")}).action_process()

    def test_views_load(self):
        for model in ("marketplace.field", "marketplace.issue", "marketplace.feedback.import"):
            self.env[model].get_views([(False, "list"), (False, "form"), (False, "search")])
        self.env["product.template"].get_views([(False, "list"), (False, "form"), (False, "search")])
